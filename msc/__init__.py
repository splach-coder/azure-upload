import azure.functions as func
import logging
import json
import os
import base64

from msc.service.pdf_service import extract_text_from_coordinates, process
from msc.config.coords import coordinates
from msc.config.data_structure import key_map
from msc.utils.text_utils import update_object
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
        # Actual code logic
        extracted_data = extract_text_from_coordinates(uploaded_file_path, coordinates, key_map)
        
        # Handle string case and parse 'data' if it's a string
        if isinstance(extracted_data, str):
            extracted_data = {"data": extracted_data}
        
        # Check if 'data' key exists and is a stringified JSON
        if 'data' in extracted_data:
            parsed_data = json.loads(extracted_data['data'])  # Parse the string in 'data'
            del extracted_data['data']  # Remove the 'data' key
            extracted_data.update(parsed_data)  # Merge parsed 'data' at the top level
        
        # Now add containers to the extracted_data
        extracted_data["containers"] = process(uploaded_file_path)

        # Step 2: Print the final JSON with proper formatting
        formatted_json = json.dumps(extracted_data, indent=4)

        formatted_json = update_object(formatted_json)

        # Delete the temporary uploaded file
        os.remove(uploaded_file_path)

    # Convert JSON to XML (kept in memory, not saved as a file)
    xml_content = json_to_xml(formatted_json)

    # If json_to_xml() returns a list, get the first item
    # If it returns a string, this line isn't necessary
    xml_string = xml_content[0] if isinstance(xml_content, list) else xml_content

    # Set the response headers to indicate an XML content type
    headers = {
        "Content-Type": "application/xml",
        "Content-Disposition": "attachment; filename=shipment_data.xml"
    }
    
    # Create the response object with the XML content
    return func.HttpResponse(
        body=xml_string,
        status_code=200,
        headers=headers
    )
