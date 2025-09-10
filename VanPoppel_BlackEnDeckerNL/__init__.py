from datetime import datetime
from AI_agents.OpenAI.custom_call import CustomCall
from ILS_NUMBER.get_ils_number import call_logic_app
import azure.functions as func
import logging
import json
import os
import openpyxl
import base64
import uuid
import re
from AI_agents.Gemeni.adress_Parser import AddressParser
from VanPoppel_BlackEnDeckerNL.excel.create_excel import write_to_excel
from VanPoppel_BlackEnDeckerNL.functions.functions import extract_clean_excel_from_pdf

import tempfile
import time
import io
import gc

def _safe_remove(path, attempts=3, delay=0.1):
    """Try to remove a file with a few retries (useful on Windows when transient locks occur)."""
    if not path:
        return
    for i in range(attempts):
        try:
            if os.path.exists(path):
                os.remove(path)
            return
        except PermissionError as e:
            logging.warning(f"PermissionError removing file {path}, attempt {i+1}/{attempts}: {e}")
            # force GC and small sleep to allow handles to close
            gc.collect()
            time.sleep(delay)
        except Exception as e:
            logging.error(f"Unexpected error removing file {path}: {e}")
            break

def merge_pdf_results(pdf_results):
    merged = {"Items": []}
    for entry in pdf_results:
        items = entry.get("Items", [])
        if isinstance(items, list):
            merged["Items"].extend(items)
    return merged

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing Stanley Excel + PDF extraction request.')

    # --- Parse request body ---
    try:
        body = req.get_json()
        files_data = body.get("files", [])
        email_data = body.get("email", "")
        if not files_data:
            raise ValueError("No files provided in 'files' array")
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": f"Invalid request format: {e}"}),
            status_code=400,
            mimetype="application/json"
        )

    # Fresh containers each call (prevents stale data)
    result_data = None
    pdf_result = None
    second_layout = False
    pdf_results = []
    # --- Loop files ---
    for file_data in files_data:
        filename = file_data.get("filename")
        file_content_base64 = file_data.get("file")

        if not filename or not file_content_base64:
            logging.warning("Skipping file without filename or content.")
            continue

        temp_file_path = None
        pdf_document = None
        workbook = None

        try:
            decoded_data = base64.b64decode(file_content_base64)

            # Use a unique temporary file name (prevents collisions)
            suffix = os.path.splitext(filename)[1] or ""
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                temp_file_path = tmp.name
                tmp.write(decoded_data)

            logging.info(f"Saved temporary file {temp_file_path}")
            file_extension = os.path.splitext(filename.lower())[1]

            # --- Handle PDF ---
            if file_extension == ".pdf":
                if "eur1" not in filename.lower():
                    import fitz  # PyMuPDF
                    try:
                        pdf_document = fitz.open(temp_file_path)  # explicit open
                        # you can also: with fitz.open(temp_file_path) as pdf_document:
                        text = ""
                        with fitz.open(pdf_document) as doc:
                            for page in doc:  # iterate over all pages
                                text += page.get_text("text") + "\n"
                        pdf_result = extract_clean_excel_from_pdf(text)
                        pdf_results.append(pdf_result)
                    finally:
                        if pdf_document is not None:
                            try:
                                pdf_document.close()
                            except Exception as close_e:
                                logging.warning(f"Error closing pdf document: {close_e}")
                            pdf_document = None

            # --- Handle Excel ---
            elif file_extension in [".xlsm", ".xlsx", ".xls"]:
                try:
                    workbook = openpyxl.load_workbook(temp_file_path, data_only=True)
                    sheet = workbook.active

                    def get_cell_value(cell_id):
                        return sheet[cell_id].value if sheet[cell_id] else None

                    def extract_number(value):
                        if isinstance(value, str):
                            numbers = re.findall(r"\d+", value)
                            return int(numbers[0]) if numbers else None
                        if isinstance(value, (int, float)):
                            return value
                        return None

                    def get_first_part(value):
                        return value.split()[0] if isinstance(value, str) else value

                    # detect layout
                    e13_value = get_cell_value("E13")
                    if isinstance(e13_value, str) and "eur1" in e13_value.lower():
                        second_layout = True

                    header_data = {
                        "reference": get_first_part(get_cell_value("B2")),
                        "invoice_number": get_first_part(get_cell_value("B3")),
                        "delivery_conditions": get_cell_value("B4"),
                        "office_of_exit": get_cell_value("B5"),
                        "country_of_destination": get_cell_value("B6"),
                        "total_amount": get_cell_value("B7"),
                        "currency": get_cell_value("B8"),
                        "pallet_info": extract_number(get_cell_value("B9")),
                        "total_gross_weight_kg": get_cell_value("B10"),
                        "total_net_weight_kg": get_cell_value("B11"),
                    }

                    client_data = {
                        "name": get_cell_value("H5"),
                        "address": get_cell_value("H6"),
                        "postal_code_city": get_cell_value("H7"),
                        "country": get_cell_value("H8"),
                    }

                    line_items = []
                    for row in sheet.iter_rows(min_row=14, min_col=2, max_col=5, values_only=True):
                        hs_code = row[0]
                        if hs_code is None:
                            break
                        try:
                            line_items.append({
                                "hs_code": str(hs_code),
                                "amount": float(row[1]) if row[1] else 0.0,
                                "gross_weight_kg": float(row[2]) if row[2] else 0.0,
                                "net_weight_kg": float(row[3]) if row[3] else 0.0,
                            })
                        except Exception:
                            continue

                    full_address = ", ".join(filter(None, [
                        str(client_data["name"]),
                        str(client_data["address"]),
                        str(client_data["postal_code_city"]),
                        str(client_data["country"])
                    ]))

                    parser = AddressParser()
                    parsed_address_list = parser.parse_address(full_address)
                    parsed_address = {
                        "company_name": parsed_address_list[0] if len(parsed_address_list) > 0 else None,
                        "street": parsed_address_list[1] if len(parsed_address_list) > 1 else None,
                        "city": parsed_address_list[2] if len(parsed_address_list) > 2 else None,
                        "postal_code": parsed_address_list[3] if len(parsed_address_list) > 3 else None,
                        "country_code": parsed_address_list[4] if len(parsed_address_list) > 4 else None,
                    }

                    result_data = {
                        "ShipmentReference": header_data.get("reference"),
                        "Incoterm": (header_data.get("delivery_conditions") or "") + " " + (parsed_address.get("city") or ""),
                        "Total Value": header_data.get("total_amount"),
                        "NetWeight": header_data.get("total_net_weight_kg"),
                        "GrossWeight": header_data.get("total_gross_weight_kg"),
                        "currency": header_data.get("currency"),
                        "Collis": header_data.get("pallet_info"),
                        "OfficeOfExit": header_data.get("office_of_exit"),
                        "PlaceOfDelivery": parsed_address,
                        "Invoice No": header_data.get("invoice_number"),
                        "Items": line_items
                    }

                    # inject ILS number
                    try:
                        response = call_logic_app("STANLEY", company="vp")
                        if response.get("success"):
                            result_data["ILS_NUMBER"] = response["doss_nr"]
                    except Exception as e:
                        logging.error(f"ILS_NUMBER fetch failed: {e}")

                finally:
                    if workbook is not None:
                        try:
                            workbook.close()
                        except Exception as e:
                            logging.warning(f"Error closing workbook: {e}")
                        workbook = None

        except Exception as outer_e:
            logging.error(f"Error processing file {filename}: {outer_e}", exc_info=True)

        finally:
            # Always attempt safe remove of temp file (with retries)
            try:
                _safe_remove(temp_file_path)
            except Exception as e:
                logging.error(f"Failed to remove temp file {temp_file_path}: {e}")
                
    # --- Merge all PDF results ---
    pdf_final_data = merge_pdf_results(pdf_results)      

    # --- Merge PDF Items into Excel Skeleton ---
    if result_data and pdf_final_data and "Items" in pdf_final_data and pdf_final_data["Items"]:
        result_data["Items"] = pdf_final_data["Items"]
        logging.info(f"Final merged {len(pdf_final_data['Items'])} items from PDF into result_data.")
        
    for item in (result_data.get("Items", []) if result_data else []):
        if "InvoiceDate" in item and isinstance(item["InvoiceDate"], str):
            # Remove any extra whitespace
            item["InvoiceDate"] = item["InvoiceDate"].replace('-', '/').strip()

    # --- Build Response ---
    if not result_data:
        return func.HttpResponse(
            body="No valid Excel or PDF data processed",
            status_code=400
        )

    try:
        prompt = f"""You will receive a raw email in HTML or plain text format. 
            Your task: extract the sender's email address, and return only the part before the "@" symbol.  

            For example:  
            - If the sender is "Ellen.Nowak@sbdinc.com", return "Ellen.Nowak".  
            - If the sender is "john_doe@example.org", return "john_doe".  

            Rules:  
            - Always return just the extracted string, no explanations.  
            - If no valid email is found, return an empty string.
            
            Here is the email body: '''{email_data}'''. """
        call = CustomCall()
        contact = call.send_request(role="user", prompt_text=prompt)
        
        result_data["Contact"] = contact.strip()[:10]
        excel_file_bytes = write_to_excel(result_data, second_layout)
        reference = result_data.get("ShipmentReference", f"ref-{uuid.uuid4().hex}")
        
        headers = {
            "Content-Disposition": f'attachment; filename="{reference}.xlsx"',
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "X-Second-Layout": str(second_layout)
        }
        # excel_file_bytes expected to be BytesIO-like
        body_bytes = excel_file_bytes.getvalue() if hasattr(excel_file_bytes, "getvalue") else bytes(excel_file_bytes)
        return func.HttpResponse(body_bytes, headers=headers)
    except Exception as e:
        logging.error(f"Error writing Excel: {e}", exc_info=True)
        return func.HttpResponse(body=f"Error: {e}", status_code=500)
