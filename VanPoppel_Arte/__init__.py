import azure.functions as func
import logging
import json
import os
import base64

import fitz

from AI_agents.Gemeni.adress_Parser import AddressParser
from VanPoppel_Arte.helpers.extractors import extract_customs_authorization_no, extract_invoice_meta_and_shipping, extract_products_from_text, extract_totals_and_incoterm
from VanPoppel_Arte.helpers.functions import clean_invoice_items, merge_invoice_outputs, safe_int_conversion
from VanPoppel_Arte.excel.create_excel import write_to_excel



def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body.get('files', [])
        body = req_body.get('body', {})

    except ValueError:
        logging.error("Invalid JSON in request body.")
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json"
        )
    
    if not files:
        logging.warning("No files provided in the request.")
        return func.HttpResponse(
            body=json.dumps({"error": "No selected files"}),
            status_code=400,
            mimetype="application/json"
        )
    
    combined_data = []

    for file_info in files:
        file_content_base64 = file_info.get('file')
        filename = file_info.get('filename', 'temp.pdf')

        if not file_content_base64:
            logging.warning(f"File '{filename}' has no content. Skipping.")
            continue

        # Decode base64
        try:
            file_content = base64.b64decode(file_content_base64)
        except Exception as e:
            logging.error(f"Failed to decode base64 for '{filename}': {e}")
            return func.HttpResponse(
                body=json.dumps({"error": "Failed to decode base64 content", "details": str(e)}),
                status_code=400,
                mimetype="application/json"
            )

        # Save temp file
        temp_dir = os.getenv('TEMP', '/tmp')
        uploaded_file_path = os.path.join(temp_dir, filename)

        try:
            with open(uploaded_file_path, 'wb') as temp_file:
                temp_file.write(file_content)
            logging.info(f"Saved file '{filename}' to '{uploaded_file_path}'.")
        except Exception as e:
            logging.error(f"Failed to write file '{filename}': {e}")
            return func.HttpResponse(
                body=json.dumps({"error": "Failed to write file to disk", "details": str(e)}),
                status_code=500,
                mimetype="application/json"
            )

        # 🧠 Open the file with fitz
        doc = fitz.open(uploaded_file_path)

        # ----------------------------------------
        # 🔹 Extract header info from first page
        # ----------------------------------------
        first_page_text = doc[0].get_text()
        header_inv_data = extract_invoice_meta_and_shipping(first_page_text)

        address = header_inv_data.get("shipping_address", "")
        parser = AddressParser()
        parsed_result = parser.parse_address(address)
        header_inv_data["shipping_address"] = parsed_result

        # ----------------------------------------
        # 🔸 Extract item lines from all pages
        # ----------------------------------------
        all_items = []
        for page in doc:
            page_text = page.get_text()
            page_items = extract_products_from_text(page_text)
            all_items.extend(page_items)
        
        # ----------------------------------------
        # 🔹 Extract header info from last page
        # ----------------------------------------
        last_page_text = doc[-1].get_text()
        footer_inv_data = extract_totals_and_incoterm(last_page_text)
        customs_no = extract_customs_authorization_no(last_page_text)
        

        # Combine and append result
        invoice_output = {
            "header": header_inv_data,
            "footer": footer_inv_data,
            "items": all_items,
            "customs_no": customs_no.upper() if customs_no else "",
        }
        
        combined_data.append(invoice_output)

    # Combine all invoices into one
    combined_result = merge_invoice_outputs(combined_data)
    
    if len(combined_result.get("items")) > 1:
        # Sort items by Customs Tariff Code
        sorted_items = sorted(combined_result.get("items"), key=lambda x: x.get("customs_tariff", ""))
        
        # Replace the original list with the sorted one
        combined_result["items"] = sorted_items      
    
    combined_result, TotalNetWeight, TotalSurface, TotalQuantity = clean_invoice_items(combined_result)
    combined_result["Totals"] = {
        "TotalNetWeight": round(TotalNetWeight, 3),
        "TotalSurface": round(TotalSurface, 3),
        "TotalQuantity": round(TotalQuantity, 3)
    }
    
    # Proceed with data processing
    try:
        logging.error("we reach here")
        excel_file= write_to_excel(combined_result)
        reference = combined_result.get("header").get("document_number")

        # Set response headers for the Excel file download
        headers = {
            'Content-Disposition': 'attachment; filename="' + reference + '.xlsx"',
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }

        # Return the Excel file as an HTTP response
        return func.HttpResponse(excel_file.getvalue(), headers=headers, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except TypeError as te:
        logging.error(f"TypeError during processing: {te}")
        return func.HttpResponse(
            body=json.dumps({"error": "Data processing failed due to type error", "details": str(te)}),
            status_code=500,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Unexpected error during processing: {e}")
        return func.HttpResponse(
            body=json.dumps({"error": "An unexpected error occurred", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )