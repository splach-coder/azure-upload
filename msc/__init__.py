import azure.functions as func
import logging
import json
import os
import base64

from msc.service.pdf_service import extract_text_from_coordinates
from msc.config.coords import coordinates
from msc.config.data_structure import key_map
from msc.utils.text_utils import data_to_json, update_object
from msc.email.sentEmail import json_to_xml

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
        
        # Decode the base64 content
        file_content = base64.b64decode(file_content_base64)
        
        # Save the uploaded file temporarily
        temp_dir = os.getenv('TEMP', '/tmp')
        uploaded_file_path = os.path.join(temp_dir, filename)

        # Write the file to the temporary path
        with open(uploaded_file_path, 'wb') as temp_file:
            temp_file.write(file_content)
        
        # Extract text from PDF based on coordinates
        extracted_text = extract_text_from_coordinates(uploaded_file_path, coordinates)
        extracted_text = data_to_json(extracted_text[1], key_map)
        extracted_text = json.loads(extracted_text)

        extracted_text = update_object(extracted_text, "Gross Weight")
        extracted_text = update_object(extracted_text, "Item")
        extracted_text = update_object(extracted_text, "Packages")

        # Delete the temporary uploaded file
        os.remove(uploaded_file_path)

    # Convert JSON to XML (kept in memory, not saved as a file)
    xml_content = json_to_xml(extracted_text)
    
    # Set the response headers to indicate an XML content type
    headers = {
        "Content-Type": "application/xml",
        "Content-Disposition": "attachment; filename=shipment_data.xml"
    }
    
    # Create the response object with the XML content
    return func.HttpResponse(
        body=xml_content,
        status_code=200,
        headers=headers
    )
