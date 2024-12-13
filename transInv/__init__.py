import azure.functions as func
import logging
import json
import os
import base64

from transInv.functions import extract_text_from_pdf

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        file = req_body.get('file', "")
        filename = req_body.get('filename', 'temp.pdf')
        
    except ValueError:
        logging.error("Invalid JSON in request body.")
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json"
        )
    
    if not file:
        logging.warning("No file provided in the request.")
        return func.HttpResponse(
            body=json.dumps({"error": "No selected files"}),
            status_code=400,
            mimetype="application/json"
        )
    
    if not filename:
        logging.warning(f"File '{filename}' has no content. Skipping.")
    
    # Decode the base64-encoded content
    try:
        file_content = base64.b64decode(file)
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
        
        logging.error(pdf_text)

        isTransInv = True if "Proforma Invoice".lower() in pdf_text.lower() or "Proforma Facture".lower() in pdf_text.lower() or "Confirmation de commande".lower() in pdf_text.lower() else False

        try:
            # Prepare the JSON response
            response = {
                "contains_invoice": isTransInv  # Sending the array of XML strings
            }

            return func.HttpResponse(
                json.dumps(response),
                mimetype="application/json",
                status_code=200
            )
    
        except Exception as e:
            logging.error(f"Error: {e}")
            return func.HttpResponse(
                f"Error processing request: {e}", status_code=500
            )

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
