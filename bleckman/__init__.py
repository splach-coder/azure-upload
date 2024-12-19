import azure.functions as func
import logging
import json
import os
import base64
import zipfile

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.ai.formrecognizer import DocumentAnalysisClient # Use this API key to call Azure Document Intelligence
from azure.core.credentials import AzureKeyCredential

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
        
    # Replace with your Key Vault URL
    key_vault_url = "https://kv-functions-python.vault.azure.net"
    secret_name = "azure-form-recognizer-key-2"  # The name of the secret you created
    
    
    # Use DefaultAzureCredential for authentication
    credential = DefaultAzureCredential()

    # Create a SecretClient to interact with the Key Vault
    client = SecretClient(vault_url=key_vault_url, credential=credential)

    # Retrieve the secret value
    try:
        api_key = client.get_secret(secret_name).value
        logging.info(f"API Key retrieved: {api_key}")
    except Exception as e:
        logging.error(f"---------------Failed to retrieve secret: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": "Failed to retrieve secret", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
    
    # Your Form Recognizer endpoint
    endpoint = "https://document-intelligence-python.cognitiveservices.azure.com/"
    #apikey = AzureKeyCredential(api_key)
    #apikey = "8jCA4tf8Tpc8FcBSYnkAAhQlB6aFWwCzl9IBmjZPQahxJjuJ1xGWJQQJ99ALAC5RqLJXJ3w3AAALACOGx8wJ"
    client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))
    
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
        voorblad_data = {}
        invoices_data = []
        invoice_type = ""
    
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
                            voorblad_data = json.loads(extract_text_from_first_page(pdf_path, coordinates, key_map))
                            
                        else:
                            if "to" in file_name.lower():
                                invoice_type = "dollar"
                                logging.info(f"Processing TO inv: {file_name}")
                            elif "if" in file_name.lower():
                                invoice_type = "euro"
                                logging.info(f"Processing TO inv: {file_name}")
                                
                            pdf_path = os.path.join(temp_dir, file_name)    
                            with open(pdf_path, "rb") as f:
                                document = f.read()

                            poller = client.begin_analyze_document("bleckman-model", document)
                            result = poller.result()

                            document = result.documents
                            result_dict = {}
                            fields = document[0].fields
                            for key, value in fields.items():
                                if key in ["Address", "Items"]:  # Fields that contain arrays
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

                            invoices_data.append(result_dict)

            # Append the processed JSON to extracted_data
            invoices_data_type = {
                **voorblad_data,
                "invoice_type": invoice_type,
                "data": invoices_data
            }              
                        
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
        body=json.dumps(invoices_data_type, indent=2),
        status_code=200,
        mimetype="application/json"
    )