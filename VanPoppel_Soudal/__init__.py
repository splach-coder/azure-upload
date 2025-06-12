import datetime
import re
import azure.functions as func
import logging
import json
import os
import base64

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.ai.formrecognizer import DocumentAnalysisClient 
from azure.core.credentials import AzureKeyCredential

from AI_agents.Gemeni.adress_Parser import AddressParser
from AI_agents.OpenAI.custom_call import CustomCall

from VanPoppel_Soudal.excel.write_to_extra_excel import write_to_extra_excel
from VanPoppel_Soudal.excel.create_sideExcel import extract_clean_excel_from_pdf
from VanPoppel_Soudal.helpers.functions import clean_incoterm, clean_customs_code, merge_factuur_objects, normalize_number, safe_float_conversion
from VanPoppel_Soudal.excel.create_excel import write_to_excel
from VanPoppel_Soudal.zip.create_zip import zip_excels 

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body.get('files', [])
        email_body = req_body.get('body', [])
        subject = req_body.get('subject', '')
        
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
        
    # Key Vault URL
    key_vault_url = "https://kv-functions-python.vault.azure.net"
    secret_name = "azure-form-recognizer-key-2"  # The name of the secret you created
    
    # Use DefaultAzureCredential for authentication
    credential = DefaultAzureCredential()

    # Create a SecretClient to interact with the Key Vault
    client = SecretClient(vault_url=key_vault_url, credential=credential)

    # Retrieve the secret value
    try:
        api_key = client.get_secret(secret_name).value
    except Exception as e:
        logging.error(f"Failed to retrieve secret: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": "Failed to retrieve secret", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
    
    # Form Recognizer endpoint
    endpoint = "https://document-intelligence-python.cognitiveservices.azure.com/"
    client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))
        
    factuur_results = []  # Array to store all factuur results
    extra_file_excel_data = None
    extra_file_excel = None
    
    for file_info in files:
        
        file_content_base64 = file_info.get('file')
        filename = file_info.get('filename', 'temp.pdf')
        
        # Extract the factuur files (multiple files possible)
        if 'factuur' in filename.lower():

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
            if not filename.lower().endswith('.pdf') and not filename.lower().endswith('.PDF'):
                logging.error(f"File '{filename}' is not a PDF. Skipping analysis.")
                continue

            logging.info(f"File '{filename}' is processing.")
            # Analyze the document
            try: 
                poller = client.begin_analyze_document("vp-soudal-model", file_content)
                result = poller.result()

                document = result.documents
                result_dict = {}
                fields = document[0].fields
                for key, value in fields.items():
                    if key in ["Items"]:  # Fields that contain arrays
                        arr = value.value
                        result_dict[key] = []
                        for item in arr:
                            value_object = item.value
                            obj = {}
                            for key_obj, value_obj in value_object.items():
                                obj[key_obj] = value_obj.value
                            result_dict[key].append(obj)
                    elif key in ["Total Gross", "Total Net"]:
                        result_dict[key] = value.content  
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
            customs_code = result_dict.get("Rex Number", "") if result_dict.get("Rex Number", "") else ""
            result_dict["Customs Code"] = clean_customs_code(customs_code)

            #switch the address country to abbr
            address = result_dict.get("Address", "")
            parser = AddressParser()
            parsed_result = parser.parse_address(address)
            result_dict["Address"] = parsed_result

            #clean the total gross and net
            result_dict["Total Gross"] = safe_float_conversion(normalize_number(result_dict.get("Total Gross", 0.0)))
            result_dict["Total Net"] = safe_float_conversion(normalize_number(result_dict.get("Total Net", 0.0)))

            #split the invoice value and seperate the currency
            invoice_value = result_dict.get("Total Value", "")
            if invoice_value:
                invoice_value = invoice_value.split(" ")
                if len(invoice_value) > 1:
                    currency = invoice_value[1]
                    invoice_value = invoice_value[0]
                    result_dict["Currency"] = currency
                else:
                    result_dict["Currency"] = ""
                    invoice_value = invoice_value[0]
                result_dict["Total Value"] = safe_float_conversion(normalize_number(invoice_value))
            else:
                result_dict["Total Value"] = 0.00
                result_dict["Currency"] = ""
        
            #clean the container number
            container_number = result_dict.get("Container", "")
            if container_number:
                container_number = container_number.replace(" ", "").replace(".", "")
                result_dict["Container"] = container_number

            # change the invoice date to date format
            invoice_date = result_dict.get("Inv Date", "")
            if invoice_date:
                    formats = ["%d.%m.%Y", "%d/%m/%Y"]  # Supported date formats
                    for date_format in formats:
                        try:
                            result_dict["Inv Date"] = datetime.datetime.strptime(invoice_date, date_format).date()
                            break  # Exit loop once successful conversion
                        except ValueError:
                            continue  # Try next format
                    else:
                        logging.error(f"Invalid date format: {invoice_date}")

            #update the numbers in the items
            items = result_dict.get("Items", "")
            cleaned_items = []

            for item in items:
                coo = item.get("COO", "")
                gross = safe_float_conversion(normalize_number(item.get("Gross Weight", 0.0)))
                net = safe_float_conversion(normalize_number(item.get("Net Weight", 0.0)))

                # Skip if COO is empty/None and both weights are 0
                if not coo or (gross == 0 and net == 0):
                    continue
                
                # Process the item
                if "(" in coo and ")" in coo:
                    item["COO"] = coo[2:].replace(" ", "").replace(")", "").replace("(", "")
                else :
                    item["COO"] = coo.replace(" ", "")
                item["Gross Weight"] = gross
                item["Net Weight"] = net

                if item.get("Value", 0.0) is not None:
                    item["Value"] = safe_float_conversion(normalize_number(item.get("Value", 0.0)))
                else:
                    item["Value"] = 0.00
                    
                item["Inv Number"] = result_dict.get("Inv Number", "")   
                item["Customs Code"] = result_dict.get("Customs Code", "")   
                item["Currency"] = result_dict.get("Currency", "")     

                cleaned_items.append(item)

            # Replace original items with cleaned list
            result_dict["Items"] = cleaned_items

            #determine weather the invoice is export or import
            subject = subject.strip()
            doc_type = "export" if "uitvoer" in subject.lower() else "import" if "invoer" in subject.lower() else "unknown"

            # Extract number right after "Uitvoer:" or "Invoer:"
            match = re.search(r'(uitvoer|invoer):\s*(\d+)', subject, re.IGNORECASE)
            reference = match.group(2) if match else None

            result_dict["File Type"] = doc_type    
            result_dict["Reference"] = reference
            result_dict["Filename"] = filename  # Add filename for identification
             
            # Add the processed factuur result to the array
            factuur_results.append(result_dict)
            logging.info(f"Successfully processed factuur file: {filename}")
             
        elif 'extra' in filename.lower():
            extra_file_excel_data = extract_clean_excel_from_pdf(file_content_base64, filename)

            extra_file_excel_data["rows"] = [
                row for row in extra_file_excel_data.get("rows", [])
                if not (('GrandTotal' in row and row['GrandTotal'] == True) or ('SubTotal' in row and row['SubTotal'] == True)) 
                and row.get("Comm. Code", "").strip()  # Exclude rows with empty "Comm. Code"
            ]

    # Check if we have any factuur results
    if not factuur_results:
        logging.warning("No factuur files were successfully processed.")
        return func.HttpResponse(
            body=json.dumps({"error": "No factuur files were successfully processed"}),
            status_code=400,
            mimetype="application/json"
        )
    
    # Extract the exit office from email body
    prompt = f"""
    Extract the exit office code from the following email. The code is typically in the format of two letters followed by digits (e.g., BE212000). Return only the code as a plain string. If no code is found, return "NOT Found". Do not include any extra text or formatting.

    Here is the email to extract the exit office code from:
    '''{email_body}'''
    """
    call = CustomCall()
    response = call.send_request(role="user", prompt_text=prompt)
    exit_office = response
    
    try:
        # After collecting all factuur_results
        if len(factuur_results) > 1:
            merged_result = merge_factuur_objects(factuur_results)
        else:
            # Use single result as before
            merged_result = factuur_results[0]
            
        if exit_office and exit_office != "NOT Found":
            # Add exit office to each merged_result
            merged_result["Exit office"] = exit_office    
        
        # Call writeExcel to generate the Excel file in memory
        excel_file = write_to_excel(merged_result)
        
        if extra_file_excel_data is not None:
            extra_result = merged_result.copy()
            extra_result["Items"] = extra_file_excel_data.get("rows", [])
            extra_file_excel = write_to_extra_excel(extra_result)
            logging.info("Generated Excel file2.")
        
        reference = merged_result.get("Reference")
        fileType = merged_result.get("File Type")
        
        # Create zip file
        if extra_file_excel is not None:
            zip_file = zip_excels(None, extra_file_excel, f"factuur_{reference}.xlsx", f"extra_{reference}.xlsx")
        else:
            zip_file = zip_excels(excel_file, extra_file_excel, f"factuur_{reference}.xlsx", f"extra_{reference}.xlsx")    

        # Set response headers for ZIP file
        headers = {
            'Content-Disposition': f'attachment; filename="{reference}.zip"',
            'Content-Type': 'application/zip',
            'x-file-type': fileType,
            'x-factuur-count': str(len(factuur_results))  # Add count of processed factuurs
        }

        # Return the ZIP as an HTTP response
        return func.HttpResponse(zip_file.getvalue(), headers=headers, mimetype='application/zip')
    
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