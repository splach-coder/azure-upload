import uuid
import azure.functions as func
import logging
import json
import os
import base64
import tempfile
import zipfile
import xlrd

from lili_maas_xls_merger.helpers.functions import merge_items, transform_json
from lili_maas_xls_merger.excel.create_excel import write_to_excel
from AI_agents.OpenAI.CustomCallWithImage import CustomCallWithImage

def safe_float(val):
    try:
        return float(val)
    except:
        return 0

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Lili Maas ZIP Merger - Started.')

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
        
        logging.error(f"Processing file: {filename}")

        if not filename.endswith('.zip') or not file_data:
            logging.error(f"Skipping file: {filename} (not a zip or missing data)")
            continue

        try:
            zip_bytes = base64.b64decode(file_data)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
                tmp_zip.write(zip_bytes)
                zip_path = tmp_zip.name
            logging.error(f"Saved zip to: {zip_path}")

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                temp_dir = tempfile.mkdtemp()
                zip_ref.extractall(temp_dir)
            logging.error(f"Extracted zip to: {temp_dir}")

            for f in os.listdir(temp_dir):
                full_path = os.path.join(temp_dir, f)
                ext = os.path.splitext(f)[1].lower()
                logging.error(f"Found file in zip: {f} (ext: {ext})")

                if ext == ".xls":
                    logging.error(f"Opening Excel file: {full_path}")
                    wb = xlrd.open_workbook(full_path)
                    data = {}

                    # Sheet 1
                    sheet1 = wb.sheet_by_index(0)
                    logging.error("Reading Sheet 1")
                    data["Contract Date"] = sheet1.cell_value(7, 6)
                    data["Contract No"] = sheet1.cell_value(8, 6)
                    data["VALUTA"] = sheet1.cell_value(21, 7)
                    
                    # Look for "INSURANCE FEE:" in column A
                    for row_idx in range(sheet1.nrows):
                        cell_value = str(sheet1.cell_value(row_idx, 0)).strip().upper()
                        if "INSURANCE FEE" in cell_value:
                            data["InsuranceFee"] = sheet1.cell_value(row_idx, 1)
                            data["InsuranceCurrency"] = sheet1.cell_value(row_idx, 2)
                            InsuranceCurrency = sheet1.cell_value(row_idx, 2)
                            break

                    items = []
                    row = 22
                    sets_sum = 0
                    while row < sheet1.nrows:
                        if sheet1.cell_value(row, 0) == "":
                            break
                        item = {
                            "Description": sheet1.cell_value(row, 0),
                            "Brand": sheet1.cell_value(row, 1),
                            "HS Code": sheet1.cell_value(row, 2),
                            "CARTON": sheet1.cell_value(row, 3),
                            "PCS": sheet1.cell_value(row, 4),
                            "SET": sheet1.cell_value(row, 5),
                            "Unit Price": sheet1.cell_value(row, 6),
                            "Amount": sheet1.cell_value(row, 7),
                            "InsuranceFee": data.get("InsuranceFee", 0),
                            "InsuranceCurrency": data.get("InsuranceCurrency", ''),
                            "VALUTA": data.get("VALUTA", '') 
                        }
                        items.append(item)
                        row += 1
                        sets_sum += item["SET"]
                        for item in items:
                            item["InsuranceAmount"] = round(item.get("InsuranceFee", 0) / sets_sum * item.get("SET", 0), 2)

                    data["Sheet1_Items"] = items

                    # Sheet 2
                    sheet2 = wb.sheet_by_index(1)
                    logging.error("Reading Sheet 2")
                    data["VAT No"] = sheet2.cell_value(14, 0)
                    data["EORI No"] = sheet2.cell_value(14, 1)

                    # Sheet 3
                    sheet3 = wb.sheet_by_index(2)
                    logging.error("Reading Sheet 3")
                    logistics = []
                    row = 19
                    while row < sheet3.nrows:
                        if sheet3.cell_value(row, 2) == "":
                            break
                        logistic_item = {
                            "Description": sheet3.cell_value(row, 2),
                            "Brand": sheet3.cell_value(row, 3),
                            "HS Code": sheet3.cell_value(row, 4),
                            "PCS": sheet3.cell_value(row, 5),
                            "SET": sheet3.cell_value(row, 6),
                            "CARTON": sheet3.cell_value(row, 7),
                            "Gross Weight": safe_float(sheet3.cell_value(row, 8)),
                            "Net Weight": safe_float(sheet3.cell_value(row, 9))
                        }
                        logistics.append(logistic_item)
                        row += 1
                        
                    data["Sheet3_Logistics"] = logistics

                    data = transform_json(data)
                    
                    #add contract number and date to the items data
                    for item in data.get("items"):
                        item["Contract No"] = data["Contract No"]
                        item["Contract Date"] = data["Contract Date"]
                        item["VAT No"] = data["VAT No"]
                        item["EORI No"] = data["EORI No"]

                    merged_data.append(data)

                elif ext in [".jpg", ".jpeg", ".png", ".bmp"]:
                    logging.error(f"Processing image file: {full_path}")
                    with open(full_path, "rb") as image_file:
                        encoded_image = base64.b64encode(image_file.read()).decode()
                        custom_call = CustomCallWithImage()
                        prompt = "From the image, find the 'Freight Charge' row, and return only the value under 'Settlement Amount'. No text, no formatting, just the number."
                        freight_from_image = custom_call.send_image_prompt(encoded_image, prompt)
                        logging.error(f"Freight from image: {freight_from_image}")
                        if freight_from_image:
                            freight_from_image = freight_from_image.replace(",", "")
                            freight_from_image = safe_float(freight_from_image)

                        
                final_version = merge_items(merged_data)
                final_version["Freight"] = freight_from_image if freight_from_image else 0.00
                final_version["Contract No"] = filename.split(" ")[0]
                final_version["InsuranceCurrency"] = InsuranceCurrency
                        
            os.remove(zip_path)

        except Exception as e:
            logging.error(f"Exception while processing file {filename}: {str(e)}")
            return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)

    try:
        # Call writeExcel to generate the Excel file in memory
        excel_file = write_to_excel(final_version)
        logging.info("Generated Excel file.")
        
        reference = final_version.get("Contract No", "") or ("Lilly_mass_" + uuid.uuid4().hex[:8])

        # Set response headers for the Excel file download
        headers = {
            'Content-Disposition': 'attachment; filename="' + reference + '.xlsx"',
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }

        # Return the Excel file as an HTTP response
        return func.HttpResponse(excel_file.getvalue(), headers=headers, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            f"Error processing request: {e}", status_code=500
        )