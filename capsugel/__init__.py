import azure.functions as func
import logging
import json
import os
import base64

from capsugel.excel.createExcel import write_to_excel
from capsugel.helpers.adress_extractors import get_address_structure
from capsugel.helpers.functions import print_json_to_file, calculate_totals, change_keys, detect_pdf_type, clean_invoice_data, clean_packing_list_data, clean_invoice_total, clean_grand_totals_in_packing_list, merge_invoice_with_packing_list, remove_g_from_date, clean_number, vat_validation
from capsugel.service.extractors import extract_customs_code_from_pdf_invoice, extract_customs_code_from_text, extract_data_from_pdf, extract_exitoffices_from_body, extract_structured_data_from_pdf_invoice, extract_text_from_last_page, extract_text_from_first_page, find_page_in_invoice, merge_incomplete_records_invoice

from capsugel.config.coords import coordinates, coordinates_be, coordinates_lastpage, key_map, inv_keyword_params, inv_keyword_params_de, fallback_inv_keywords, packingList_keyword_params
from capsugel.data.countries import countries
from capsugel.data.keys import invoice_keys, packing_list_keys, invoice_keys_de
from capsugel.service.language_detection import detect_language

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
    
    data_packinglist = []
    combined_data = None

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
        
        language = detect_language(uploaded_file_path)
        logging.info(f"Detected PDF language for '{filename}': {language}")
        
        pdf_type = detect_pdf_type(uploaded_file_path)
        logging.info(f"Detected PDF type for '{filename}': {pdf_type}")

        # Handle the detected PDF type
        if pdf_type == "Packing List":
            extracted_data = extract_data_from_pdf(uploaded_file_path, packingList_keyword_params)
            if not extracted_data:
                logging.error(f"Extraction failed for Packing List PDF: {filename}")
                continue  # Or handle as needed
            try:
                extracted_data = clean_packing_list_data(json.loads(extracted_data))
                extracted_data = change_keys(extracted_data, packing_list_keys)
                data_packinglist.extend(clean_grand_totals_in_packing_list(extracted_data))
                logging.info(f"Extracted Packing List data from '{filename}'.")
            except json.JSONDecodeError as jde:
                logging.error(f"JSON decoding failed for Packing List PDF '{filename}': {jde}")
                return func.HttpResponse(
                    body=json.dumps({"error": "Invalid JSON in Packing List PDF", "details": str(jde)}),
                    status_code=400,
                    mimetype="application/json"
                )
        elif pdf_type == "Invoice":
            try:
                coors_for_invoice = coordinates_be if language == "de" else coordinates
                data_1 = json.loads(extract_text_from_first_page(uploaded_file_path, coors_for_invoice, key_map))
                
                data_1["Vat"] = vat_validation(data_1["Vat"])
                data_1["Inv Date"] = remove_g_from_date(data_1["Inv Date"])
                data_1["Inv Ref"] = clean_number(data_1["Inv Ref"])
                data_1["ship to"] = get_address_structure(data_1["ship to"], countries)
                
                if("(INCOTERMS 2010)" in data_1["Inco"]) or ("Incoterms:" in data_1["Inco"]) or ("(INCOTERMS 2010" in data_1["Inco"]):
                    data_1["Inco"] = data_1["Inco"].replace("(INCOTERMS 2010)", '')
                    data_1["Inco"] = data_1["Inco"].replace("Incoterms:", '')
                data_1["Inco"] = data_1["Inco"].split(' ', 1)
                
                if len(data_1["Inco"]) == 1:
                    data_1["Inco"].append("")  
                
                if language == "de":
                    lst_keywords=["Rechnungsbetrag", "MwSt", "Fälliger Rechnungsbetrag", "* Letzte Seite"]
                else:
                    lst_keywords=["Invoice Total Net", "Total VAT", "Total Value Due", "* Last Page"]

                page = find_page_in_invoice(uploaded_file_path, lst_keywords)
                data_2 = json.loads(extract_text_from_last_page(uploaded_file_path, coordinates_lastpage, page[0], ["invoice"]))
                data_2 = clean_invoice_total(data_2)

                items_inv_keywords_params = inv_keyword_params_de if language == "de" else inv_keyword_params
                data_3 = extract_structured_data_from_pdf_invoice(uploaded_file_path, items_inv_keywords_params, fallback_inv_keywords)
                data_3 = merge_incomplete_records_invoice(data_3)
                data_3 = clean_invoice_data(data_3, countries)
                
                keyword_params={"Bevorzugter Text:" : ((700, 30), -200)} if language == "de" else {"Preferential Text:" : ((700, 30), -200)}
                data_4 = extract_customs_code_from_pdf_invoice(uploaded_file_path, keyword_params)
                
                customs_code = "Bevorzugter Text:" if language == "de" else "Preferential Text:"
                
                data_4 = extract_customs_code_from_text(data_4.get(customs_code, ""))
                
                combined_invoice_data = {**data_1, **data_2, "customs_code": data_4.replace(" ", ""), "items": data_3}
                
                keys_general_inv = invoice_keys_de if language == "de" else invoice_keys
                combined_data = change_keys(combined_invoice_data, keys_general_inv)
                              
                logging.info(f"Extracted Invoice data from '{filename}'.")

            except json.JSONDecodeError as jde:
                logging.error(f"JSON decoding failed for Invoice PDF '{filename}': {jde}")
                return func.HttpResponse(
                    body=json.dumps({"error": "Invalid JSON in Invoice PDF", "details": str(jde)}),
                    status_code=400,
                    mimetype="application/json"
                )
            except Exception as e:
                logging.error(f"Failed to extract Invoice data from '{filename}': {e}")
                return func.HttpResponse(
                    body=json.dumps({"error": "Failed to extract Invoice data", "details": str(e)}),
                    status_code=500,
                    mimetype="application/json"
                )
        else:
            logging.info(f"File '{filename}' is neither Packing List nor Invoice. Skipping.")

    # Validate that both data_packinglist and combined_data are set
    if data_packinglist is None:
        logging.error("Packing List data is missing.")
        return func.HttpResponse(
            body=json.dumps({"error": "Packing List PDF is missing or failed to process"}),
            status_code=400,
            mimetype="application/json"
        )

    if combined_data is None:
        logging.error("Invoice data is missing.")
        return func.HttpResponse(
            body=json.dumps({"error": "Invoice PDF is missing or failed to process"}),
            status_code=400,
            mimetype="application/json"
        )

    # Proceed with data processing
    try:
        merged_data = merge_invoice_with_packing_list(combined_data, data_packinglist)

        #calculate totals and merge them with the json data
        totals = calculate_totals(merged_data)
        merged_data = {**merged_data, **totals}
        
        # Extract valid codes from the body texts
        valid_codes = extract_exitoffices_from_body(body)
        #asssign it to the global json data
        merged_data['Exit Port BE'] = valid_codes

        # Call writeExcel to generate the Excel file in memory
        excel_file = write_to_excel(merged_data)
        logging.info("Generated Excel file.")

        ref = merged_data.get('Inv Ref', '')
        reference = "no-ref" if ref == '' else ref

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
