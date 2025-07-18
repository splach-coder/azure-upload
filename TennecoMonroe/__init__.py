import ast
import azure.functions as func
import logging
import json
import os
import base64

import fitz

from AI_agents.Gemeni.adress_Parser import AddressParser
from AI_agents.OpenAI.CustomCallWithPdf import CustomCallWithPdf
from AI_agents.OpenAI.custom_call import CustomCall
from ILS_NUMBER.get_ils_number import call_logic_app
from TennecoMonroe.helpers.functions import abbr_countries_in_items, add_inv_date_to_items, check_invoice_in_pdf, clean_VAT, clean_data_from_texts_that_above_value, handle_terms_into_arr, merge_pdf_data, normalize_the_items_numbers, normalize_the_totals_type
from TennecoMonroe.service.extractors import extract_dynamic_text_from_pdf, extract_freight_and_exit_office_from_html, extract_text_from_first_page, find_customs_authorisation_coords, find_page_in_invoice
from TennecoMonroe.helpers.adress_extractors import get_address_structure
from TennecoMonroe.excel.createExcel import write_to_excel
from global_db.extractors.functions import extract_Exitoffice

from TennecoMonroe.config.coords import first_page_coords, totals_page_coords
from TennecoMonroe.config.key_maps import first_page_key_map, totals_page_key_map, table_page_key_map
from global_db.countries.countries import countries

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body.get('files', [])
        body = req_body.get('body', [])
        subject = req_body.get('subject', [])

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
        
    multiple_invoices = [] 
    goods_location = ""
    merged_data = {}   

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
        
        inv = check_invoice_in_pdf(uploaded_file_path)
        if inv:  
            '''------------------- Extract the Static Values from the first page ------------------'''
            # extract the file and put it on global for multiple files case
            first_page_data = json.loads(extract_text_from_first_page(uploaded_file_path, first_page_coords, first_page_key_map, useVatBackup=True))
            #logging.error(first_page_data)
            #extract the the adress into company name, street, city ....
            address = first_page_data.get("Address")
            parser = AddressParser()
            parsed_result = parser.parse_address(address)
            #first_page_data["Address"] = get_address_structure(first_page_data["Address"])
            first_page_data["Address"] = parsed_result
            #clean the VAT from other chars
            first_page_data["Vat"] = clean_VAT(first_page_data["Vat"])
            first_page_data["Customer NO"] = clean_data_from_texts_that_above_value(first_page_data["Customer NO"])
            first_page_data["Inv Date"] = clean_data_from_texts_that_above_value(first_page_data["Inv Date"])
            first_page_data["Inv No"] = clean_data_from_texts_that_above_value(first_page_data["Inv No"])


            '''------------------- Extract the Total from the last page ---------------------------'''
            #detect which page the totals are
            totals_page = find_page_in_invoice(uploaded_file_path)
            #extract data from the totals page
            totals_data = extract_text_from_first_page(uploaded_file_path, totals_page_coords, totals_page_key_map, totals_page)
            #cast it to json
            totals_data = json.loads(totals_data)
            #update the numbers type
            totals_data = normalize_the_totals_type(totals_data)
            totals_data["Terms"] = handle_terms_into_arr(totals_data["Terms"])


            '''------------------- Extract the Table data from its page ---------------------------'''
            #extract data from the table
            x_coords = [(37, 91), (91, 156), (156, 216), (216, 266), (266, 344)]  # Static x-coordinates
            y_range = (178, 188)  # Dynamic y-coordinates

            #find the table page
            table_page = find_page_in_invoice(uploaded_file_path, keywords=["Customs Tariff", "Origin", "Net Weight", "Quantity", "Value Payable"])
            # Call the function

            result = extract_dynamic_text_from_pdf(uploaded_file_path, x_coords, y_range, table_page_key_map, table_page)
            
            #------------------- Extract items with AI ---------------------------'''
            pdf_document = fitz.open(uploaded_file_path)
    
            # Get the first page
            table_page_text = pdf_document[table_page[0] - 1].get_text("text")

            prompt = (
                f"Extract all items from this text in the following JSON array format ONLY:\n\n"
                f"[{{'HS code': '...', 'Origin': '...', 'Net': ..., 'Quantity': ..., 'Value': ...}}]\n\n"
                f"Rules:\n"
                f"- Only extract lines under the table with headers: 'Customs Tariff Code', 'Origin', 'Net Weight (KG)', 'Quantity Items', 'Value Payable'\n"
                f"- Skip any totals or summary rows like 'Free Circulation Totals'\n"
                f"- Do not merge or miss any rows\n"
                f"- Use ISO 2-letter country codes for Origin (e.g. Spain → ES, Germany → DE)\n"
                f"- Replace commas in numbers with dots where needed (e.g. 1.894,012 → 1894.012)\n"
                f"- Return numeric fields as numbers (float or int), not strings\n"
                f"- Your output must be ONLY the JSON array — no explanation, no formatting, no extra text\n\n"
                f"Be very precise, do not omit or add extra data.\n\n"
                f"Text to process:\n{table_page_text}"
            )
            
            call = CustomCall()
            extracted_items = call.send_request("user", prompt)
            extracted_items = ast.literal_eval(extracted_items)

            #cast it to json
            #result = json.loads(extracted_items)
            #update countries to abbr
            #result = abbr_countries_in_items(result, countries)
            #update the numbers type
            #result = normalize_the_items_numbers(result)
            result = add_inv_date_to_items(extracted_items, first_page_data.get("Inv No", ""))


            '''------------------- Extract the Code BE70 from its page ---------------------------'''
            customs_code = find_customs_authorisation_coords(uploaded_file_path, table_page)


            '''------------------- JOIN data in one object - items also ---------------------------'''
            all_data = {**first_page_data, **totals_data, "Customs Code" : customs_code, "items" : result}


            '''------------------- append the data list to the global var --------------------------'''
            multiple_invoices.append(all_data)

            '''------------------- Extract data from the subject line --------------------------'''
            goods_location = extract_Exitoffice(subject)

    
    if multiple_invoices:
        '''------------------- merging the data to be one object --------------------------'''
        merged_data = merge_pdf_data(multiple_invoices)
        
        '''------------------- Add the goods location to the object --------------------------'''
        merged_data["Goods Location"] = goods_location
        
        '''------------------- Extract the mail from the email --------------------------'''
        body = body.replace(subject, "")
        body = body.replace(merged_data.get("Goods Location", ""), "")
        result = extract_freight_and_exit_office_from_html(body)
        
        merged_data["Exit office"] = result["exit_office"]
        merged_data["Freight"] = result["freight"]
        merged_data["Container"] = result["Container"]
        
        
        try:
            # Get the ILS number
            response = call_logic_app("TENNECOSTR")
    
            if response["success"]:
                merged_data["ILS_NUMBER"] = response["doss_nr"]
            else:
                logging.error(f"❌ Failed to get ILS_NUMBER: {merged_data['error']}")
    
        except Exception as e:
            logging.exception(f"💥 Unexpected error while fetching ILS_NUMBER: {str(e)}")  
        
    # Proceed with data processing
    try:
        # Call writeExcel to generate the Excel file in memory
        excel_file = write_to_excel(merged_data)
        logging.info("Generated Excel file.") 
        
        reference = merged_data.get("Inv No", "")
        reference = reference.replace('Invoice no.', '').replace('\n', '')


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