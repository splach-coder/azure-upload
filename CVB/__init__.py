import logging
import azure.functions as func
import json

from CVB.functions.functions import build_items, detect_sender_flow, extract_email_body, extract_info_from_email, extract_info_from_proforma, extract_text_from_pdf
from CVB.excel.create_excel import write_to_excel 

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('CVB Import Flow Parser - Started')

    try:
        body = req.get_json()
        base64_files = body.get('files', [])
        email_body = body.get('email', '')
    except Exception:
        return func.HttpResponse(json.dumps({"error": "Invalid request format"}), status_code=400)

    if not base64_files:
        return func.HttpResponse(json.dumps({"error": "No files provided"}), status_code=400)

    result = {}
    result["AnnexAvailability"] = False

    for file_obj in base64_files:
        filename = file_obj.get("filename", "").lower()
        content = file_obj.get("file", "")

        if "proforma" in filename and "invoice" in filename:
            text = extract_text_from_pdf(content)
            try:
                proforma_info = extract_info_from_proforma(text)
                if isinstance(proforma_info, str):
                    proforma_info = json.loads(proforma_info)
                elif isinstance(proforma_info, dict):
                    proforma_info = proforma_info
                    
                result.update(proforma_info)    
            except Exception as e:
                logging.error(f"AI extraction failed: {e}")

        elif "annex" in filename:
            result["AnnexAvailability"] = True
    
    #clean the email body from any HTML tags
    email_body = extract_email_body(email_body)    
            
    # detect the company based on the filename  
    company = detect_sender_flow(email_body)

    result["Company"] = company

    # Handle email body parsing
    try:
        email_data = extract_info_from_email(email_body)
        if isinstance(email_data, str):
            email_data = json.loads(email_data)
        elif isinstance(email_data, dict):
            email_data = email_data
            
        result.update(email_data)     
    except Exception as e:
        logging.error(f"Failed to extract from email body: {e}")
        
    # Handle the Freight and VAT calculations based on the company 
    if company == 'williamsrecycling':
        cost = result.get("TransportCosts", 0)
        freight = cost * 0.70  # 70% of cost
        vat = cost * 0.30      # 30% of cost
        result["Freight"] = freight
        result["VAT"] = vat
    elif company == 'coolsolutions':
        result["Freight"] = result.get("TransportCosts").get("UK", 0)
        result["VAT"] = result.get("TransportCosts").get("Belgium", 0)    
    
    # Build items array from the result
    result = build_items(result)
    
    # Proceed with data processing
    try:
            
        excel_file = write_to_excel(result)
        logging.info("Generated Excel file.")
        
        reference = result.get("InvoiceRef", "")

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