import azure.functions as func
import logging
import json
import os
import base64

from ferminich.excel.create_excel import write_to_excel
from ferminich.helpers.adress_extractors import get_address_structure
from ferminich.helpers.functions import clean_invoice_text, combine_invoices, get_currency_abbr, get_inco_arr, normalise_number, safe_float_conversion
from ferminich.service.extrators import clean_array_from_unwanted_items, extract_and_clean, extract_cleaned_invoice_text, extract_customs_code_from_text, extract_fields_from_item_text, extract_information, extract_invoice_details, extract_optional_from_pdf_invoice, extract_text_from_first_page, extract_vat_number, split_items_into_array, vat_validation

from ferminich.coords.coords import header_inv_coords
from ferminich.coords.keys import header_inv_keys
from ferminich.data.countries import countries  


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body.get('files', [])
        body = req_body.get('body', {})

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
            
        """------------------------- Extract data from pdf invoice with coordinations-------------------------"""  
        header_inv_data = json.loads(extract_text_from_first_page(uploaded_file_path, header_inv_coords, header_inv_keys))
        #extract vat 
        header_inv_data["Vat"] = vat_validation(extract_vat_number(header_inv_data["Vat"]))
        #extract the address
        header_inv_data["Address"] = get_address_structure(header_inv_data["Address"], countries)
        #extract the currency
        header_inv_data["Currency"] = get_currency_abbr(header_inv_data["Currency"])
        #extract the currency
        header_inv_data["Inco"] = get_inco_arr(header_inv_data["Inco"])
        
        
        """------------------------- Extract items data from pdf invoice-------------------------"""  
        invoice_pages = extract_cleaned_invoice_text(uploaded_file_path) 

        for key, value in invoice_pages.items():
            invoice_pages[key] = clean_invoice_text(value)
                          
        items_data = extract_invoice_details(invoice_pages)

        array_of_items = split_items_into_array(items_data)
        array_of_items = clean_array_from_unwanted_items(array_of_items)

        items_data = extract_fields_from_item_text(array_of_items)
        
        for item in items_data:
            item["Inv Ref"] = header_inv_data["Inv Ref"]
        
        """------------------------- Extract totals data from pdf invoice-------------------------"""
        keyword_params_total={"Total Amount Payable" : ((700, 0), 200)}
        total_inv = extract_optional_from_pdf_invoice(uploaded_file_path, keyword_params_total)
        if total_inv:
            total_inv = total_inv['Total Amount Payable'].split("\n")
        
            if len(total_inv) > 1:
                total_inv[1] = safe_float_conversion(normalise_number(total_inv[1]))
        else:
            total_inv = ['', 0.00]   
        
        
        """------------------------- Extract items data from pdf invoice-------------------------"""
        keyword_params_customs_code={"The exporter of the product" : ((700, 0), -200)}
        keyword_params_customs_code_text = extract_optional_from_pdf_invoice(uploaded_file_path, keyword_params_customs_code)
        keyword_params_customs_code = extract_customs_code_from_text(keyword_params_customs_code_text)
        
        
        """------------------------- append all data to the global arr for multiple files -------------------------"""
        pdf_file_data = {**header_inv_data, "customs code" : keyword_params_customs_code, "items" : items_data, "total" : total_inv}
        combined_data.append(pdf_file_data)
        
    """Combine data in one object"""
    result = combine_invoices(combined_data)    
            
    '''Extract the body data''' 
    cleaned_email_body_html = extract_and_clean(body)
    
    if cleaned_email_body_html:
        email_body = extract_information(body)
        
    else :
        email_body = {"reference": '', "colis": '', "weight": '', "location": ''}
    
    
    """Add the email data to the result"""
    result = {**email_body, **result}
            
    # Proceed with data processing
    try:
        excel_file= write_to_excel(result)
        reference = result["reference"]

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
        
