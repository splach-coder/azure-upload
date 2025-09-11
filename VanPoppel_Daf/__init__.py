import azure.functions as func
import logging
import json

# --- Imports for Splitting Logic & Your Helpers ---
from AI_agents.OpenAI.custom_call import CustomCall

from ILS_NUMBER.get_ils_number import call_logic_app
from VanPoppel_Daf.excel.create_sideExcel import extract_clean_excel_from_pdf, get_invoice_page_number, extract_specific_page_as_base64
from VanPoppel_Daf.excel.create_excel import write_to_excel


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    try:
        req_body = req.get_json()
        files = req_body.get('files', [])
        email_body = req_body.get('body', [])
        subject = req_body.get('subject', '')
    except ValueError:
        return func.HttpResponse(body=json.dumps({"error": "Invalid JSON"}), status_code=400, mimetype="application/json")
    
    if not files:
        return func.HttpResponse(body=json.dumps({"error": "No selected files"}), status_code=400, mimetype="application/json")
        
    extra_file_excel_data = None
    call = CustomCall()
    
    for file_info in files:
        file_content_base64 = file_info.get('file')
        filename = file_info.get('filename', 'temp.pdf')

        # Get invoice page number from AI
        invoice_page_number = get_invoice_page_number(file_content_base64, filename)
        logging.error(f"Determined invoice page number: {invoice_page_number} for file: {filename}")

        # Process based on invoice page number
        if invoice_page_number == 0:
            # No invoice found - this is a barcode-only file
            logging.error(f"No invoice found in {filename} - skipping Excel extraction")
            continue
        else:
            # Extract the specific invoice page
            try:
                # Check if page 2 needs rotation
                rotate_needed = False

                # Extract only the invoice page
                invoice_page_base64 = extract_specific_page_as_base64(
                    file_content_base64, 
                    invoice_page_number, 
                    rotate_right=rotate_needed
                )

                # Send only the invoice page for Excel extraction
                extra_file_excel_data = extract_clean_excel_from_pdf(invoice_page_base64, filename)
                logging.error(extra_file_excel_data)

            except Exception as e:
                logging.error(f"Error processing invoice page {invoice_page_number} from {filename}: {str(e)}")
                continue
        
    try:
        prompt = f"""Your task is to read an export-instruction e-mail and extract all shipment data into a structured JSON object.

{email_body}

The e-mails are written in Dutch and contain repeating patterns. Even if some words vary slightly, you must always capture the following fields when present:

- Exporter Name (from "Naam afzender/exporteur")
- Exporter EORI Number (from "Eori-nummer afzender/exporteur")
- Exporter VAT Number (from "Btw-nummer afzender/exporteur")
- Invoice Number (from "Factuurnummer")
- Unit ID (from "Unit ID")
- Partial Shipment (from "Deelzending")
- Booking Number (from "boekingsnummer")
- Office of Exit (from "Kantoor van uitgang")
- Cabins (from lines like "x CABINES")
- Gross Weight (kg) (from lines like "BRUTO KG")
- Value (€) (from lines like "= €...")

Instructions:
- Always output the result as valid JSON.
- If a field is missing, set its value to null.
- Normalise numbers (strip units like "KG", "€") but keep them as strings.
- Do not skip any detail, even if wording or formatting changes.

Example output:
  {{
    "Exporter Name": "DAF TRUCKS NV",
    "Exporter EORI Number": "NL801426972",
    "Exporter VAT Number": "BE08766688176",
    "Invoice Number": "58485889",
    "Unit ID": "FZA-70408",
    "Partial Shipment": "Deelzending 2",
    "Booking Number": "PONFEU05219050",
    "Office of Exit": "Rotterdam", only the city name
    "Cabins": 5, should be integer
    "Gross Weight": 7406, should be float
    "Value": 94269.45  should be float
  }}
""" 
        call = CustomCall()
        email_data = call.send_request(role="You are an information extraction assistant.", prompt_text=prompt)
        # Clean response
        raw = email_data.replace("```", "").replace("json", "").strip()
        parsed = json.loads(raw)
        
        # calc the Net Weight Total
        try:
            Total_Net_Weight = 0.0
            for item in extra_file_excel_data.get("Items", []):
                if "NETT_WEIGHT" in item:
                    Total_Net_Weight += item["NETT_WEIGHT"]
            extra_file_excel_data["Total Net"] = Total_Net_Weight
        except Exception as e:  
            logging.error(f"Error calculating Total Net Weight: {e}")
            extra_file_excel_data["Total Net"] = 0.00        

        merged_result = {**extra_file_excel_data, **parsed}

        excel_file = write_to_excel(merged_result)
        reference = merged_result.get("Booking Number")
        
        headers = {
            'Content-Disposition': f'attachment; filename="{reference}.xlsx"',
            'Content-Type': 'application/excel',
        }
        return func.HttpResponse(excel_file.getvalue(), headers=headers, mimetype='application/excel', status_code=200)
    
    except Exception as e:
        logging.error(f"Unexpected error during final processing: {e}")
        return func.HttpResponse(body=json.dumps({"error": "An unexpected error occurred during final processing", "details": str(e)}), status_code=500, mimetype="application/json")