import azure.functions as func
import logging
import json
import os
import base64
import zipfile

from bleckman.service.extractors import extract_text_from_first_page
from bleckman.config.keywords import key_map, coordinates

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body.get('files', [])
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
    
    for file_info in files:
        file_content_base64 = file_info.get('file')
        filename = file_info.get('filename', 'temp.zip')  # Assuming zip file

        if not file_content_base64:
            logging.warning(f"File '{filename}' has no content. Skipping.")
            continue
        
        # Decode the base64-encoded content
        try:
            file_content = base64.b64decode(file_content_base64)
        except Exception as e:
            logging.error(f"Failed to decode base64 content for file '{filename}': {e}")
            return func.HttpResponse(
                body=json.dumps({"error": "Failed to decode base64 content", "details": str(e)}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Save the uploaded file temporarily
        temp_dir = os.getenv('TEMP', '/tmp')  # Use temp directory
        uploaded_file_path = os.path.join(temp_dir, filename)

        # Write the file to the temporary path
        try:
            with open(uploaded_file_path, 'wb') as temp_file:
                temp_file.write(file_content)
            logging.info(f"Saved file '{filename}' to '{uploaded_file_path}'.")
        except Exception as e:
            logging.error(f"Failed to write file '{filename}' to disk: {e}")
            return func.HttpResponse(
                body=json.dumps({"error": "Failed to write file to disk", "details": str(e)}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Initialize a list to store extracted PDF data
        extracted_data = []
        
        # Unzip the file and process PDFs
        try:
            with zipfile.ZipFile(uploaded_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)  # Extract files to temp directory

                for file_name in zip_ref.namelist():
                    logging.info(f"Found file: {file_name}")
                    # Check if the file is a PDF
                    if file_name.endswith('.pdf'):
                        pdf_path = os.path.join(temp_dir, file_name)
                        
                        if "Voorblad" in file_name:
                            logging.info(f"Processing Voorblad PDF: {file_name}")
                            # Process Voorblad PDFs (custom logic here)

                            extracted_data = extract_text_from_first_page(pdf_path, coordinates, key_map)
                        else:
                            logging.info(f"Processing regular PDF: {file_name}")
                            # Process regular PDFs  
                        
        except zipfile.BadZipFile as e:
            logging.error(f"Failed to unzip file '{filename}': {e}")
            return func.HttpResponse(
                body=json.dumps({"error": "Failed to unzip file", "details": str(e)}),
                status_code=400,
                mimetype="application/json"
            )

        # Cleanup temp file
        os.remove(uploaded_file_path)
    
    # Set response as JSON with extracted data
    return func.HttpResponse(
        body=extracted_data,
        status_code=200,
        mimetype="application/json"
    )