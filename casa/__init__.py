import azure.functions as func
import logging
import json
import os
import base64

from casa.excel.create_excel import generate_excel_zip
from casa.helpers.functions import hanlde_country
from casa.service.extractors import clean_and_convert_totals, clean_invoice_data, extract_cleaned_invoice_text, extract_container_load_plan_text, extract_header_details, extract_items_from_text, extract_totals_from_text, extract_vissel_details, get_items_data, merge_data

from casa.data.data import ports

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
        
        Items_All = []

        invoice_pages = extract_cleaned_invoice_text(uploaded_file_path)
        invoice_pages = clean_invoice_data(invoice_pages)
        
        '''Extract the Header Details (origin, inco terms invoice date, vissel)'''
        header_details = extract_header_details(invoice_pages)
        header_details = hanlde_country(header_details, ports)
        
        '''Extract the Container Load Plan text'''
        vissel_data = extract_container_load_plan_text(uploaded_file_path)
        vissel = extract_vissel_details(vissel_data)
        
        '''Extract Totals from the text'''
        #totals_data = extract_totals_from_text(invoice_pages)
        #totals_data = clean_and_convert_totals(totals_data)
        
        '''Extract ing items from the text'''
        for key, text in invoice_pages.items():
            texto = extract_items_from_text(text)
            for item in texto:
                item_obj = get_items_data(item)
                Items_All.append({"Invoice_Number" : key, **item_obj})
                
        '''Merge the items data into one object'''        
        result = merge_data(Items_All, vissel, header_details)
        
    # Proceed with data processing
    try:
        container_key = ""
        for item in result: container_key += item['container']
        
        # Generate the ZIP file containing Excel files
        zip_data = generate_excel_zip(result)
        logging.info("Generated Excel file.")

        # Return the ZIP file as a response
        return func.HttpResponse(
            zip_data,
            mimetype="application/zip",
            headers={"Content-Disposition": 'attachment; filename="files-' + container_key + '".zip'}
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
