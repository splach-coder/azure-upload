import azure.functions as func
import logging
import json
import os
import base64

from evgr.service.extractdata import extract_text_from_pages, extract_text_from_pdf
from evgr.config.coords import coordinates, coordinates_2



def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body.get('files', [])
    except ValueError:
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json"
        )
    
    if not files:
        return func.HttpResponse(
            body=json.dumps({"error": "No selected files"}),
            status_code=400,
            mimetype="application/json"
        )

    for file_info in files:
        file_content_base64 = file_info.get('file')
        filename = file_info.get('filename', 'temp.pdf')

        if not file_content_base64:
            continue
        
        # Decode the base64-encoded content
        try:
            file_content = base64.b64decode(file_content_base64)
        except Exception as e:
            return func.HttpResponse(
                body=json.dumps({"error": "Failed to decode base64 content", "details": str(e)}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Save the uploaded file temporarily
        temp_dir = os.getenv('TEMP', '/tmp')
        uploaded_file_path = os.path.join(temp_dir, filename)

        # Write the file to the temporary path
        with open(uploaded_file_path, 'wb') as temp_file:
            temp_file.write(file_content)

        # Actual code logic
        extracted_data = extract_text_from_pdf(uploaded_file_path, coordinates, coordinates_2)

        # Actual code logic
        extracted_data = extract_text_from_pages(uploaded_file_path, coordinates)
        
    try:
        # Prepare the JSON response
        response = {
            "xml_files": extracted_data  # Sending the array of XML strings
        }

        return func.HttpResponse(
            extracted_data,
            mimetype="application/json",
            status_code=200
        )
    
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            f"Error processing request: {e}", status_code=500
        )
