import azure.functions as func
import logging
import json
import os
import base64

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

from Crosby.excel.createExcel import write_to_excel
from Crosby.helpers.functions import change_date_format, clean_customs_code, clean_incoterm, clean_numbers, combine_invoices_by_address, extract_reference, extract_totals_info, fill_origin_country_on_items, is_invoice, normalize_number, process_email_location, safe_float_conversion, safe_int_conversion
from global_db.countries.functions import get_abbreviation_by_country
from global_db.functions.numbers.functions import normalize_numbers

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')
    
    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body.get('files', [])
        email = req_body.get("body", '')
        subject = req_body.get("subject", '')
        
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
        
    # Key Vault and Form Recognizer setup
    key_vault_url = "https://kv-functions-python.vault.azure.net"
    secret_name = "azure-form-recognizer-key-2"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=key_vault_url, credential=credential)

    # Retrieve the secret value
    try:
        api_key = client.get_secret(secret_name).value
        logging.info(f"API Key retrieved: {api_key}")
    except Exception as e:
        logging.error(f"Failed to retrieve secret: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": "Failed to retrieve secret", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
    
    endpoint = "https://document-intelligence-python.cognitiveservices.azure.com/"
    client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))
    
    results = []
    
    for file_info in files:
        file_content_base64 = file_info.get('file')
        filename = file_info.get('filename', 'temp.pdf')

        if not file_content_base64:
            logging.warning(f"File '{filename}' has no content. Skipping.")
            continue
        
        # Decode the base64-encoded content
        try:
            file_content = base64.b64decode(file_content_base64)
            logging.info(f"Decoded content length for file '{filename}': {len(file_content)}")
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
            
        # Validate the file format (optional)
        if not filename.lower().endswith('.pdf'):
            logging.error(f"File '{filename}' is not a PDF. Skipping analysis.")
            continue
        
        # Validate the file format (optional)
        # if not is_invoice(filename):
        #     logging.error(f"File '{filename}' is not an invoice. Skipping analysis.")
        #     continue
        
        # Analyze the document
        try: 
            poller = client.begin_analyze_document("Crosby-model", file_content)
            result = poller.result()
            
            document = result.documents
            result_dict = {}
            fields = document[0].fields
            for key, value in fields.items():
                if key in ["Adrress", "Items", "Totals"]:  # Fields that contain arrays
                    arr = value.value
                    result_dict[key] = []
                    for item in arr:
                        value_object = item.value
                        obj = {}
                        for key_obj, value_obj in value_object.items():
                            obj[key_obj] = value_obj.value
                        result_dict[key].append(obj)
                else:
                    result_dict[key] = value.value
       
        except Exception as e:
            logging.error(f"Error during document analysis for '{filename}': {e}")
            return func.HttpResponse(
                body=json.dumps({"error": "Document analysis failed", "details": str(e)}),
                status_code=500,
                mimetype="application/json"
            )   
        
        '''------------------   Clean the JSON response   ------------------ '''
        #clean and split the incoterm
        result_dict["Incoterm"] = clean_incoterm(result_dict.get("Incoterm", ""))
        
        #clean the customs code
        customs_code = result_dict.get("Customs Code", "") if result_dict.get("Customs Code", "") else ""
        result_dict["Customs Code"] = clean_customs_code(customs_code)
        
        #switch the address country to abbr
        address = result_dict.get("Adrress", "")[0]
        address["Country"] = get_abbreviation_by_country(address.get("Country", ""))    
            
        #update the numbers in the items
        items = result_dict.get("Items", "")  
        for item in items :
            item["Qty"] = safe_int_conversion(item.get("Qty", 0))
            item["Gross"] = safe_float_conversion(normalize_number(item.get("Gross", 0.0)))
            item["Net"] = safe_float_conversion(normalize_number(item.get("Net", 0.0)))
            item["Amount"] = safe_float_conversion(normalize_numbers(item.get("Amount", 0.0).replace("€", "").replace("$", "")))
            item["Inv Ref"] = result_dict.get("Inv Ref", "")
            
        items = fill_origin_country_on_items(items)

        #update the numbers in the items
        totals = result_dict.get("Totals", "")
        if totals:
            for item in totals :
                item["Total Qty"] = safe_int_conversion(item.get("Total Qty", 0))
                item["Total Gross"] = safe_float_conversion(normalize_number(item.get("Total Gross", 0.0)))
                item["Total Net"] = safe_float_conversion(normalize_number(item.get("Total Net", 0.0)))
                item["Total Amount"] = safe_float_conversion(normalize_numbers(item.get("Total Amount", 0.0).replace("€", "").replace("$", "")))
            
        results.append(result_dict)  
        
    results = combine_invoices_by_address(results)
    
    '''------------------Extract data from mail body-----------------------'''
    if email:
        email_data = extract_totals_info(email)
        if email_data.get("Freight", "") is not None and email_data.get("Collis", "") is not None:
            email_data["Freight"] = safe_float_conversion(clean_numbers(email_data.get("Freight", "")))
            email_data["Collis"] = safe_int_conversion(email_data.get("Collis", ""))
            goodsLocationCode = process_email_location(email)
            if goodsLocationCode.get("found", ""):
                email_data["Goods Location"] = goodsLocationCode.get("postal_code", "")
                 
    reference = ""
    if subject: 
        reference = extract_reference(subject).replace('/', '-')
    
    for item in results:    
        item["Reference"] = reference
        item["Email"] = email_data  

    for inv in results:  
        prev_date = inv.get('Inv Date', '')
        new_date = change_date_format(prev_date)
        inv["Inv Date"] = new_date

    logging.error(json.dumps(results, indent=4))
    
    # Proceed with data processing
    try:
        # Generate the ZIP file containing Excel files
        zip_data = write_to_excel(results)
        logging.info("Generated Zip folder.")

        # Return the ZIP file as a response
        return func.HttpResponse(
            zip_data,
            mimetype="application/zip",
            headers={"Content-Disposition": 'attachment; filename="' + reference + '".zip'}
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