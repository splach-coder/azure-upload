import azure.functions as func
import logging
import json
import os
import base64

from marken.config.keys import keys
from marken.config.coords import coords
from marken.helpers.functions import list_to_json, merge_json_objects
from marken.service.extractors import extract_and_clean, extract_email_data, extract_text_from_coordinates, find_correct_pdf
from marken.helpers.adress_extractors import get_address_structure
from marken.excel.excel import write_to_excel

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body.get('files', [])
        email_body = req_body.get('body', "")
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
        filename = file_info.get('filename', 'temp.pdf')

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
        temp_dir = os.getenv('TEMP', '/tmp')
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

    # Proceed with data processing
    try:
        #check if the right pdf or ignore
        if find_correct_pdf(uploaded_file_path) :
            #process the pdf file
            marken_extracted_text = extract_text_from_coordinates(uploaded_file_path, coords)
            #make json from the pdf extracted data
            marken_json_data = list_to_json(marken_extracted_text, keys)
            marken_json_data['Adress'] = get_address_structure(marken_json_data['Adress'])

            #process the email body
            # Extract data from the email body
            email_extracted_data = extract_and_clean(email_body)
            email_extracted_data = extract_email_data(email_extracted_data)

            #merged the email and marken pdf data together
            merged_data = merge_json_objects(marken_json_data, email_extracted_data)

            # Write the extracted data to an Excel file
            excel_file = write_to_excel(merged_data)
            logging.info("Generated Excel file.")

            Referentienummer = marken_json_data.get('Marken_reference', '')

            # Set response headers for the Excel file download
            headers = {
                'Content-Disposition': 'attachment; filename="' + Referentienummer + '.xlsx"',
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
