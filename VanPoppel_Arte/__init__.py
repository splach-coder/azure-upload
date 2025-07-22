import azure.functions as func
import logging
import json
import os
import base64

import fitz

from AI_agents.Gemeni.adress_Parser import AddressParser
from AI_agents.OpenAI.custom_call import CustomCall
from ILS_NUMBER.get_ils_number import call_logic_app
from VanPoppel_Arte.helpers.extractors import extract_customs_authorization_no, extract_customs_code, extract_invoice_meta_and_shipping, extract_products_from_text, extract_totals_and_incoterm, find_page_in_invoice
from VanPoppel_Arte.helpers.functions import clean_invoice_items, extract_email_body, merge_invoice_outputs, safe_float_conversion, safe_int_conversion
from VanPoppel_Arte.excel.create_excel import write_to_excel


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body.get('files', [])
        email = req_body.get('email', {})

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
    
    combined_data = []

    for file_info in files:
        file_content_base64 = file_info.get('file')
        filename = file_info.get('filename', 'temp.pdf')

        if not file_content_base64:
            logging.warning(f"File '{filename}' has no content. Skipping.")
            continue

        # Decode base64
        try:
            file_content = base64.b64decode(file_content_base64)
        except Exception as e:
            logging.error(f"Failed to decode base64 for '{filename}': {e}")
            return func.HttpResponse(
                body=json.dumps({"error": "Failed to decode base64 content", "details": str(e)}),
                status_code=400,
                mimetype="application/json"
            )

        # Save temp file
        temp_dir = os.getenv('TEMP', '/tmp')
        uploaded_file_path = os.path.join(temp_dir, filename)

        try:
            with open(uploaded_file_path, 'wb') as temp_file:
                temp_file.write(file_content)
            logging.info(f"Saved file '{filename}' to '{uploaded_file_path}'.")
        except Exception as e:
            logging.error(f"Failed to write file '{filename}': {e}")
            return func.HttpResponse(
                body=json.dumps({"error": "Failed to write file to disk", "details": str(e)}),
                status_code=500,
                mimetype="application/json"
            )

        # 🧠 Open the file with fitz
        doc = fitz.open(uploaded_file_path)

        # ----------------------------------------
        # 🔹 Extract header info from first page
        # ----------------------------------------
        first_page_text = doc[0].get_text()
        header_inv_data = extract_invoice_meta_and_shipping(first_page_text)

        address = header_inv_data.get("shipping_address", "")
        parser = AddressParser()
        parsed_result = parser.parse_address(address)
        header_inv_data["shipping_address"] = parsed_result
        
        address2 = header_inv_data.get("billing_address", "")
        parsed_result2 = parser.parse_address(address2)
        header_inv_data["billing_address"] = parsed_result2
        
        # ----------------------------------------
        # 🔸 Extract item lines from all pages
        # ----------------------------------------
        all_items = []
        for page in doc:
            page_text = page.get_text()
            page_items = extract_products_from_text(page_text)
            all_items.extend(page_items)
        
        # ----------------------------------------
        # 🔹 Extract Footer info from last page
        # ----------------------------------------
        page = find_page_in_invoice(doc)
        last_page_text = doc[page[0]-1].get_text()
        footer_inv_data = extract_totals_and_incoterm(last_page_text)
        
        
        
        # ----------------------------------------
        # 🔹 Extract Customs Code info from last page
        # ----------------------------------------
        page = find_page_in_invoice(doc, ["customs", "The exporter of the products"])
        customs_no = None
        try:
            customs_page_text = doc[page[0]-1].get_text()
            customs_no = extract_customs_code(customs_page_text)
        except:
            logging.error("Customs authorization number not found or page extraction failed.")
            
            
        # ----------------------------------------
        # 🔹 Address handle
        # ----------------------------------------
        #call chatgpt class
        call = CustomCall()
        
        finalDestination_page = find_page_in_invoice(doc, ["FINAL DESTINATION"])
        
        if type(finalDestination_page) is not str:

            finalDestination_text = doc[finalDestination_page[0]-1].get_text()
            
            role_forCountryDestination = "You are a data extraction agent. Your task is to extract the FINAL DESTINATION county from this text"
            prompt_forCountryDestination = f"""
            Extract the FINAL DESTINATION county as 2 letters abbreviation if country panama return pa from the following text and return it as a single string without any additional text or formatting.
            
            Text :
            \"\"\"
            {finalDestination_text}
            \"\"\"
            """
            country = call.send_request(role_forCountryDestination, prompt_forCountryDestination)
            country = country.strip().upper()
            
            if country.lower() == header_inv_data["billing_address"][-1].lower():
                header_inv_data["address"] = header_inv_data["billing_address"] 
            else :
                header_inv_data["address"] = header_inv_data["shipping_address"] 
        else :
            shipping_address_country = header_inv_data.get("shipping_address", [])[-1] if header_inv_data.get("shipping_address") not in [None, ""] else ""

            #ask if the shipping address is in the EU countries
            role_forEuCountries = "You are a factual AI that only responds with True or False based on whether a given country is a member of the European Union (EU). Your responses must be strictly Python boolean values: True if the country is an EU member, False if not. No explanations, no extra text — just True or False"
            prompt_forEuCountries = f"Is \"{shipping_address_country}\" a member of the European Union? Respond only with True or False as a Python boolean"
            memberOfEU = call.send_request(role_forEuCountries, prompt_forEuCountries)

            #cast to bool
            memberOfEU_bool = str(memberOfEU).strip() == "True"
    
            if memberOfEU_bool:
                #logging.error("m in billing address")
                header_inv_data["address"] = header_inv_data["billing_address"] 
            else :
                #logging.error("m in shipping address")
                header_inv_data["address"] = header_inv_data["shipping_address"]  
                       
        # Combine and append result
        invoice_output = {
            "header": header_inv_data,
            "footer": footer_inv_data,
            "items": all_items,
            "customs_no": customs_no.upper() if customs_no else "",
        }
        
        combined_data.append(invoice_output)

    # Combine all invoices into one
    for doc in combined_data:
        for item in doc.get("items"):
            item["document_number"] = doc.get("header").get("document_number")
    
    combined_result = merge_invoice_outputs(combined_data)
    
    if len(combined_result.get("items")) > 1:
        # Sort items by Customs Tariff Code
        sorted_items = sorted(combined_result.get("items"), key=lambda x: x.get("customs_tariff", ""))
        
        # Replace the original list with the sorted one
        combined_result["items"] = sorted_items      
    
    email = extract_email_body(email)
    role = "You are a data extraction agent. Your task is to extract specific logistics fields from the body of an email and return them in flat JSON format. The fields include truck, exit_office, colli, and gross_weight. If a field is missing, return its value as null. All numeric values must be returned as numbers without units like KG or P."
    prompt = f"""
        Extract the following fields from the email body and return the result as pure JSON only. Do not include any explanation or formatting.

        Fields to extract:
        - truck (e.g. 'DUTCHQARGO')
        - exit_office (e.g. 'NL000432')
        - colli (as number, e.g. 2)
        - gross_weight (as number, no KG) be aware of the comma it not a separator but a decimal point (e.g. 123,56)

        Email body:
        \"\"\"
        {email}
        \"\"\"
        """
    
    email_data = call.send_request(role, prompt)
    
    email_data = json.loads(email_data)
    
    combined_result, TotalNetWeight, TotalSurface, TotalQuantity = clean_invoice_items(combined_result)
    
    combined_result["Totals"] = {
        "TotalNetWeight": round(TotalNetWeight, 3),
        "TotalSurface": round(TotalSurface, 3),
        "TotalQuantity": round(TotalQuantity, 3)
    }
    combined_result["email_data"] = email_data
    
    try:
        # Get the ILS number
        response = call_logic_app("ARTE", company="vp") 

        if response["success"]:
            combined_result["ILS_NUMBER"] = response["doss_nr"]
            logging.info(f"ILS_NUMBER: {combined_result['ILS_NUMBER']}")
        else:
            logging.error(f"❌ Failed to get ILS_NUMBER: {response['error']}")
    
    except Exception as e:
        logging.exception(f"💥 Unexpected error while fetching ILS_NUMBER: {str(e)}")
    
    # Proceed with data processing
    try:
        excel_file= write_to_excel(combined_result)
        reference = combined_result.get("header").get("document_number")

        # Set response headers for the Excel file download
        headers = {
            'Content-Disposition': 'attachment; filename="' + reference + '.xlsx"',
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