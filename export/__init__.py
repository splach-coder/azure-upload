import azure.functions as func
import logging
import json
import os
import base64

from export.helpers.functions import write_to_excel, extract_key_value_pairs, extract_text_from_pdf, modify_and_correct_amounts, extract_body_text, extract_office_value, updateBTWnumber, updateAdress

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
        body = file_info.get('body')
        filename = file_info.get('filename', 'temp.pdf')

        if not file_content_base64:
            logging.warning(f"File '{filename}' has no content. Skipping.")
            continue

        if not body:
            logging.warning(f"Body has no content. Skipping.")
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
        # Extract text from the PDF
        pdf_text = extract_text_from_pdf(uploaded_file_path)

        # Parse the extracted text into key-value pairs
        parsed_data = extract_key_value_pairs(pdf_text)
        
        parsed_data = modify_and_correct_amounts(parsed_data)

        parsed_data = updateBTWnumber(parsed_data)

        parsed_data = updateAdress(parsed_data, pdf_text)

        Referentienummer = json.loads(parsed_data)["Referentienummer"]

        body_number = extract_office_value(extract_body_text(body))

        # Write the extracted data to an Excel file
        excel_file = write_to_excel(parsed_data, body_number)

        logging.info("Generated Excel file.")

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
