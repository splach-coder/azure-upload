from typing import List
import azure.functions as func
import logging
import json
import os
import base64

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

from AI_agents.Gemeni.email_Parser import EmailParser
from AI_agents.Gemeni.adress_Parser import AddressParser
from AI_agents.Gemeni.functions.functions import convert_to_list
from AI_agents.OpenAI.custom_call import CustomCall
from ILS_NUMBER.get_ils_number import call_logic_app
from cg_europe.excel.createExcel import write_to_excel
from cg_europe.helpers.functions import change_date_format, clean_number, extract_clean_email_body, clean_vat_number, clean_customs_code, clean_incoterm, combine_invoices_by_address, extract_ref, extract_text_from_pdf, extract_totals_info,  normalize_number, safe_float_conversion, safe_int_conversion
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

        # Extract text from the PDF
        pdf_text = extract_text_from_pdf(uploaded_file_path)

        is_CG_Inv = True if "Customs Information".lower() in pdf_text.lower() and "GC EUROPE N.V.".lower() in pdf_text.lower() else False

        skip_file = False
        
        # Validate the file format (optional)
        if not is_CG_Inv:
            logging.error(f"File '{filename}' is not an invoice. Skipping analysis.")
            skip_file = True
            continue
        
        if not skip_file:
            # Analyze the document
            try: 
                poller = client.begin_analyze_document("Gc-europe-model4", file_content)
                result = poller.result()
                
                document = result.documents
                result_dict = {}
                fields = document[0].fields

                for key, value in fields.items():
                    
                    if key in ["Items", "Address"]:  # Fields that contain arrays
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
            
            logging.info(f"Extracted data from '{filename}': {result_dict}")
            #clean and split the incoterm
            result_dict["Incoterm"] = clean_incoterm(result_dict.get("Incoterm", ""))

            #clean and split the incoterm
            result_dict["Vat Number"] = clean_vat_number(result_dict.get("Vat Number", ""))

            #clean the customs code
            customs_code = result_dict.get("Customs Code", "") if result_dict.get("Customs Code", "") else ""
            result_dict["Customs Code"] = clean_customs_code(customs_code)

            #Handle Inv Reference
            if result_dict.get("Inv Reference") is None and result_dict.get("Other Ref") is not None:
                result_dict["Inv Reference"] = result_dict.get("Other Ref")
            elif result_dict.get("Inv Reference") is None and result_dict.get("Other Ref") is None:
                result_dict["Inv Reference"] = ""
                result_dict["Other Ref"] = ""

            #switch the address country to abbr
            if len( result_dict.get("Address", "")) > 0:
                address = result_dict.get("Address", "")[0]
                parser = AddressParser()
                address = parser.format_address_to_line_old_addresses(address)
                parsed_result = parser.parse_address(address)
                result_dict["Address"] = parsed_result

            #update the type of Gross weight Total
            result_dict["Gross weight Total"] = safe_float_conversion(normalize_numbers(result_dict.get("Gross weight Total", 0.0)))

            #update the type of Total 
            result_dict["Total"] = safe_float_conversion(normalize_numbers(result_dict.get("Total", 0.0)))

            #update the numbers in the items
            items = result_dict.get("Items", "")  
            for item in items :
                item["Qty"] = safe_int_conversion(item.get("Qty", 0))
                item["Gross"] = safe_float_conversion(normalize_number(item.get("Gross", 0.0)))
                item["Net"] = safe_float_conversion(normalize_number(item.get("Net", 0.0)))
                item["Amount"] = safe_float_conversion(normalize_numbers(item.get("Amount", 0.0).replace("€", "").replace("$", "")))
                item["Inv Ref"] = result_dict.get("Inv Reference", "")
    
            results.append(result_dict)  
    
    results = combine_invoices_by_address(results)
    if "Total Net" not in results:
        for inv in results : 
            inv["Total Net"] = sum(item.get("Net", 0) for item in inv.get("Items", []))

    
    '''------------------Extract data from mail body-----------------------'''            
    if email : 
        # Extract data from the email body
        parser = CustomCall()
        email = extract_clean_email_body(email)
        role = "You are a data extraction assistant. Your task is to read input text and extract specific fields as structured JSON. Always respond ONLY with a raw JSON object without any extra text or explanation. If a required field is missing, return it as null."
        prompt_text = f""" Extract and return ONLY a JSON object with the following fields:

            - reference: value starting with "CI" followed by numbers (example: "CI 1170592"). If not found, return null.
            - pallets: the number of pallets or collis mentioned (example: "1 Pallets" or "1 colli") extract only the number in int format.
            - weight: the weight mentioned in KG (example: "114,59 KG" or "0.86 KG").
            - template_name: the location found after "Locatie" or "Locatie goederen" (example: ["Wijnegem", "Maasmechelen", "MM", "WY"]) Note : if it's an abbr MM or WY return the complete word (if it's MM then it's Maasmechelen and if it's WY the it's Wijnegem) .
            - exit_office: the value after "Kantoor van Uitgang" that must be 2 letters followed by 6 digits (example: "DK003102"). If not matching this pattern, return null.

            Email body:
            ---
                {email.lower()}
            --- 
            """
        parsed_result = parser.send_request(role, prompt_text)
        parsed_result = convert_to_list(parsed_result)
        parsed_result["GoodsLocation"] = parsed_result.get("template_name", "")
        parsed_result["Collis"] = safe_int_conversion(parsed_result.get("pallets", ""))
        parsed_result["Weight"] = safe_float_conversion(normalize_number(clean_number(parsed_result.get("weight", ""))))
        
        for item in results:
            item["Email"] = parsed_result

    # Extract the ref
    temp_ref = results[0].get('Email', {}).get('reference', '')
    reference = extract_ref(subject) or temp_ref

    for inv in results:  
        if inv.get("Inv Reference") is None:
            inv['Inv Reference'] = inv.get("Other Ref")
        prev_date = inv.get('Inv Date', '')
        if prev_date is not None:
            new_date = change_date_format(prev_date)
        else:
            new_date = ""
        inv["Inv Date"] = new_date
        inv["Reference"] = reference
        
    try:
        # Get the ILS number
        response = call_logic_app("CORNEEL")
        
        if response["success"]:
            results[0]["ILS_NUMBER"] = response["doss_nr"]
            logging.info(f"ILS_NUMBER: {results[0]['ILS_NUMBER']}")
        else:
            logging.error(f"Failed to get ILS_NUMBER: {response['error']}")
    
    except Exception as e:
        logging.exception(f"Unexpected error while fetching ILS_NUMBER: {str(e)}")    
    
    # Proceed with data processing
    try:
        # Generate the ZIP file containing Excel files
        excel_file = write_to_excel(results)
        logging.info("Generated Excel file.")

        # Set response headers for the Excel file download
        headers = {
            'Content-Disposition': 'attachment; filename="' + reference + '.xlsx"',
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }

               # Return the Excel file as an HTTP response
        return func.HttpResponse(excel_file, headers=headers, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

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