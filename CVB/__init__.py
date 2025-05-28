import logging
import azure.functions as func
import json

from CVB.functions.functions import extract_info_from_email, extract_info_from_proforma, extract_text_from_pdf 

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('CVB Import Flow Parser - Started')

    try:
        body = req.get_json()
        base64_files = body.get('files', [])
        email_body = body.get('body', '')
    except Exception:
        return func.HttpResponse(json.dumps({"error": "Invalid request format"}), status_code=400)

    if not base64_files:
        return func.HttpResponse(json.dumps({"error": "No files provided"}), status_code=400)

    result = {}
    result["AnnexAvailability"] = False

    for file_obj in base64_files:
        filename = file_obj.get("filename", "").lower()
        content = file_obj.get("file", "")

        if "proforma" in filename:
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

    
    excel_file = write_to_excel(result)
    return func.HttpResponse(json.dumps(result, indent=4), mimetype="application/json")