import re
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

from lili_maas_Anker_xls_merger.helpers.functions import fetch_exchange_rate
from lili_maas_Anker_xls_merger.excel.create_excel import write_to_excel

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
    
    data = {}
    
    for file in base64_files:
        filename = file.get('filename')
        file_data = file.get('file')
        
        logging.info(f"Processing file: {filename}")

        if not filename or not file_data:
            logging.error(f"Skipping file: {filename} (missing filename or data)")
            continue

        ext = os.path.splitext(filename)[1].lower()
        

        try:
            if ext == ".xlsx" and "invoice" in filename.lower():
                logging.info(f"Processing Excel file: {filename}")
                file_bytes = base64.b64decode(file_data)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
                    tmp_file.write(file_bytes)
                    excel_path = tmp_file.name
                logging.info(f"Saved Excel file to: {excel_path}")

                try:
                    wb = xlrd.open_workbook(excel_path)
                    sheet = wb.sheet_by_index(0)  # first sheet only
                    logging.info("Reading first sheet only")
 
                    try:
                        data["INVOICENUMBER"] = sheet.cell_value(7, 12)
                    except:
                        data["INVOICENUMBER"] = ""
                        
                    try:
                        data["INVOICEDATE"] = sheet.cell_value(7, 12)
                    except:
                        data["INVOICEDATE"] = ""
                        
                    try:
                        data["VATNO"] = sheet.cell_value(12, 2)
                    except:
                        data["VATNO"] = ""
                        
                    try:
                        data["EORI"] = sheet.cell_value(13, 2)
                    except:
                        data["EORI"] = ""
                        
                        
                    items = []
                    row = 23
                    while row < sheet.nrows:
                        try:
                            HSCODE = sheet.cell_value(row, 0)
                            if not HSCODE or not re.match(r"^\d{4,}$", str(HSCODE).strip()):
                                break
                            item = {
                                "HS CODE": HSCODE,
                                "DESCRIPTION OF GOODS": sheet.cell_value(row, 1),
                                "QUANTITY-SET": sheet.cell_value(row, 2),
                                "UNIT PRICE": sheet.cell_value(row, 3),
                                "TOTAL VALUE": sheet.cell_value(row, 4),
                                "VALUTA": sheet.cell_value(row, 5),
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

                    data["invoice_items"] = items
                finally:
                    del wb  # Ensure workbook is deleted and file handle is released
                    gc.collect()  # Force garbage collection
                    time.sleep(0.1)  # Short delay to ensure file handle is released
                    try:
                        os.remove(excel_path)
                    except Exception as e:
                        logging.error(f"Could not remove temp file {excel_path}: {e}")

            elif ext == ".xlsx" and "packlist" in filename.lower():
                logging.info(f"Processing Excel file: {filename}")
                file_bytes = base64.b64decode(file_data)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
                    tmp_file.write(file_bytes)
                    excel_path = tmp_file.name
                logging.info(f"Saved Excel file to: {excel_path}")

                try:
                    wb = xlrd.open_workbook(excel_path)
                    sheet = wb.sheet_by_index(0)  # first sheet only
                    logging.info("Reading first sheet only")
                        
                    items = []
                    row = 23
                    while row < sheet.nrows:
                        try:
                            Desc = sheet.cell_value(row, 5)
                            if not Desc:
                                break
                            item = {
                                "CARTON": safe_float(sheet.cell_value(row, 9)),
                                "QUANTITY-SET": safe_float(sheet.cell_value(row, 6)),
                                "GROSS": safe_float(sheet.cell_value(row, 8)),
                                "NET": safe_float(sheet.cell_value(row, 7)),
                            }
                            items.append(item)
                            row += 1
                        except Exception as e:
                            logging.error(f"Error processing row {row + 1}: {e}")
                            row += 1
                            continue

                    data["packinglist_items"] = items
                finally:
                    del wb  # Ensure workbook is deleted and file handle is released
                    gc.collect()  # Force garbage collection
                    time.sleep(0.1)  # Short delay to ensure file handle is released
                    try:
                        os.remove(excel_path)
                    except Exception as e:
                        logging.error(f"Could not remove temp file {excel_path}: {e}")

            else:
                logging.info(f"Skipping file: {filename} (unsupported type)")
                continue

        except Exception as e:
            logging.error(f"Exception while processing file {filename}: {str(e)}")
            return func.HttpResponse(json.dumps({"error": f"Error processing {filename}: {str(e)}"}), status_code=500)

    with open(os.path.join("data_dump.json" ), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        
    try:       
        excel_file = write_to_excel(data)
        logging.info("Generated Excel file.")
        
        reference = data.get("INVOICENUMBER", "") or ("Lilly_mass_" + uuid.uuid4().hex[:8])

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
