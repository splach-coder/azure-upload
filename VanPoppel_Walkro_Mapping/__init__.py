import re
import azure.functions as func
import logging
import json
import uuid

from VanPoppel_Walkro_Mapping.helpers.extractors import extract_clean_excel_from_pdf
from VanPoppel_Walkro_Mapping.helpers.functions import safe_int_conversion, safe_float_conversion
from VanPoppel_Walkro_Mapping.excel.create_excel import write_to_excel

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body.get('files', [])
        email_body = req_body.get('body', [])
        subject = req_body.get('subject', '')
        
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

    data = None
    
    for file_info in files:
        file_content_base64 = file_info.get('file')
        filename = file_info.get('filename', 'temp.pdf')
        
        data = extract_clean_excel_from_pdf(file_content_base64, filename)
        TotalValue = 0.00
        TotalCollis = 0.00
        TotalNet = 0.00
        for item in data.get('Items', []):
            item['Package'] = safe_int_conversion(re.sub(r'\D', '', item.get('Package', '')))
            TotalValue += safe_float_conversion(item.get("Invoice value", 0.0))
            TotalCollis += safe_float_conversion(item.get("Package", 0.0))
            TotalNet += safe_float_conversion(item.get("Net weight", 0.0))
            
        data['Total Value'] = TotalValue
        data['Total Pallets'] = TotalCollis
        data['Total Net'] = TotalNet    
            
    try:
        logging.error(data)
        excel_file= write_to_excel(data)
        
        # Generate a random UUID
        my_uuid = uuid.uuid4().hex[:8]
        reference = my_uuid

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