import uuid
import azure.functions as func
import logging
import json
import os
import base64
import tempfile
import xlrd
import gc
import time

from lili_maas_Bedshe_xls_merger.helpers.functions import fetch_exchange_rate
from lili_maas_Bedshe_xls_merger.excel.create_excel import write_to_excel
from AI_agents.OpenAI.CustomCallWithImage import CustomCallWithImage

def safe_float(val):
    try:
        return float(val)
    except:
        return 0.0

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Lili Maas JSON File Merger - Started.')

    try:
        body = req.get_json()
        base64_files = body.get('files', [])
    except Exception:
        return func.HttpResponse(json.dumps({"error": "Invalid request format"}), status_code=400)

    if not base64_files:
        return func.HttpResponse(json.dumps({"error": "No files provided"}), status_code=400)

    merged_data = []
    freight_from_image = None
    InsuranceCurrency = None
    
    for file in base64_files:
        filename = file.get('filename')
        file_data = file.get('file')
        
        logging.info(f"Processing file: {filename}")

        if not filename or not file_data:
            logging.error(f"Skipping file: {filename} (missing filename or data)")
            continue

        ext = os.path.splitext(filename)[1].lower()

        try:
            if ext == ".xlsx" and "combined" in filename.lower():
                logging.info(f"Processing Excel file: {filename}")
                file_bytes = base64.b64decode(file_data)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xls") as tmp_file:
                    tmp_file.write(file_bytes)
                    excel_path = tmp_file.name
                logging.info(f"Saved Excel file to: {excel_path}")

                try:
                    wb = xlrd.open_workbook(excel_path)
                    sheet = wb.sheet_by_index(0)  # first sheet only
                    logging.info("Reading first sheet only")

                    data = {}
                    try:
                        data["INVOICENUMBER"] = sheet.cell_value(1, 8)
                    except:
                        data["INVOICENUMBER"] = ""
                    try:
                        data["VATNO"] = sheet.cell_value(9, 1)
                    except:
                        data["VATNO"] = ""
                    try:
                        data["EORI"] = sheet.cell_value(8, 1)
                    except:
                        data["EORI"] = ""
                        
                    items = []
                    row = 16
                    while row < sheet.nrows:
                        try:
                            description = sheet.cell_value(row, 1)
                            if not description:
                                break
                            item = {
                                "DESCRIPTION OF GOODS": description,
                                "HS CODE": sheet.cell_value(row, 2),
                                "Material": sheet.cell_value(row, 3),
                                "CARTON": safe_float(sheet.cell_value(row, 4)),
                                "QUANTITY-SET": safe_float(sheet.cell_value(row, 5)),
                                "ASIN": safe_float(sheet.cell_value(row, 6)),
                                "UNIT PRICE": safe_float(sheet.cell_value(row, 13)),
                                "TOTAL VALUE": safe_float(sheet.cell_value(row, 14)),
                                "VALUTA": sheet.cell_value(row, 12),
                                "GROSS": safe_float(sheet.cell_value(row, 9)),
                                "NET": safe_float(sheet.cell_value(row, 10)),
                                "Sales Link": sheet.cell_value(row, 16),
                                "INVOICENUMBER": data.get("INVOICENUMBER", ""),
                                "INVOICEDATE": data.get("INVOICEDATE", ""),
                                "VATNO": data.get("VATNO", ""),
                                "EORI": data.get("EORI", "")
                            }
                            items.append(item)
                            row += 1
                        except Exception as e:
                            logging.error(f"Error processing row {row + 1}: {e}")
                            row += 1
                            continue

                    data["items"] = items
                    merged_data.append(data)
                finally:
                    del wb  # Ensure workbook is deleted and file handle is released
                    gc.collect()  # Force garbage collection
                    time.sleep(0.1)  # Short delay to ensure file handle is released
                    try:
                        os.remove(excel_path)
                    except Exception as e:
                        logging.error(f"Could not remove temp file {excel_path}: {e}")

            elif ext in [".jpg", ".jpeg", ".png", ".bmp"]:
                logging.info(f"Processing image file: {filename}")
                image_bytes = base64.b64decode(file_data)
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_image:
                    tmp_image.write(image_bytes)
                    image_path = tmp_image.name

                with open(image_path, "rb") as image_file:
                    encoded_image = base64.b64encode(image_file.read()).decode()
                    custom_call = CustomCallWithImage()
                    prompt = ("From the image, find the 'Freight Charge' row, "
                              "and return only the value under 'Settlement Amount'. "
                              "No text, no formatting, just the number without currency.")
                    freight_from_image = custom_call.send_image_prompt(encoded_image, prompt)
                    logging.info(f"Extracted freight from image: {freight_from_image}")
                    if freight_from_image:
                        freight_from_image = freight_from_image.replace(",", "")
                        freight_from_image = safe_float(freight_from_image)
                os.remove(image_path)
            else:
                logging.info(f"Skipping file: {filename} (unsupported type)")
                continue

        except Exception as e:
            logging.error(f"Exception while processing file {filename}: {str(e)}")
            return func.HttpResponse(json.dumps({"error": f"Error processing {filename}: {str(e)}"}), status_code=500)

    
    if not merged_data:
        return func.HttpResponse(json.dumps({"error": "No valid Combined .xls files found to process"}), status_code=400)
    
    try:
        # Assuming you want to merge and transform the JSON data
        final_version = merged_data[0]
        InsuranceCurrency = final_version.get("items", [{}])[0].get("VALUTA", "")
        
        

        # If you want to add freight_from_image info to final_version
        if freight_from_image is not None:
            final_version["FreightFromImage"] = freight_from_image

        try:
            final_version["ExchangeCalc"] = fetch_exchange_rate(InsuranceCurrency)
            logging.error(final_version.get("ExchangeCalc"))
        except ZeroDivisionError:
            final_version["ExchangeCalc"] = 0.0
               
        excel_file = write_to_excel(final_version)
        logging.info("Generated Excel file.")
        
        reference = final_version.get("INVOICENUMBER", "") or ("Lilly_mass_" + uuid.uuid4().hex[:8])

        headers = {
            'Content-Disposition': f'attachment; filename="{reference}.xlsx"',
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }

        return func.HttpResponse(
            excel_file.getvalue(),
            headers=headers,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        logging.error(f"Error generating final output: {e}")
        return func.HttpResponse(
            json.dumps({"error": f"Error processing request: {e}"}),
            status_code=500
        )
