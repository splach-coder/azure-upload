import azure.functions as func
import logging
import json
import os

from msc.service.pdf_service import extract_text_from_coordinates
from msc.config.coords import coordinates
from msc.config.data_structure import key_map
from msc.utils.text_utils import data_to_json, update_object

from msc.email.sentEmail import json_to_xml

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to get files from the request
    try:
        files = req.files.getlist('files')
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": "No file part in the request"}),
            status_code=400,
            mimetype="application/json"
        )

    if not files:
        return func.HttpResponse(
            body=json.dumps({"error": "No selected files"}),
            status_code=400,
            mimetype="application/json"
        )

    for file in files:
        if file.filename == '':
            continue

        # Check if the file is a PDF
        if file and file.filename.endswith('.pdf'):

           # Save the uploaded file temporarily
            temp_dir = os.getenv('TEMP', '/tmp')  # Get the temporary directory in Azure Functions
            uploaded_file_path = os.path.join(temp_dir, file.filename)  # Use the temp directory path

            # Write the file to the temporary path
            with open(uploaded_file_path, 'wb') as temp_file:
                temp_file.write(file.read())  # Write the contents of the file
            
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
