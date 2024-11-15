import azure.functions as func
import logging
import json
import os
import base64

from sofidel.helpers.adress_extractors import get_address_structure
from sofidel.helpers.excel_operations import write_to_excel
from sofidel.helpers.functions import combine_data_with_material_code, combine_data_with_material_code_collis, detect_pdf_type, find_page_with_cmr_data, handle_cmr_data, handle_invoice_data, list_to_json
from sofidel.service.extractors import extract_table_data_with_dynamic_coordinates, extract_text_from_coordinates, handle_body_request, extract_cmr_collis_data_with_dynamic_coordinates
from sofidel.config.coords import cmr_coordinates, invoice_coordinates, cmr_adress_coords, cmr_totals_coords

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body.get('files', [])
        email_body = req_body.get('body')
    except ValueError:
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json"
        )
    
    if not files:
        return func.HttpResponse(
            body=json.dumps({"error": "No selected files"}),
            status_code=400,
            mimetype="application/json"
        )

    cmr_data_glb, table_data, inv_data = None, None, None

    for file_info in files:
        file_content_base64 = file_info.get('file')
        filename = file_info.get('filename', 'temp.pdf')

        if not file_content_base64:
            continue
        
        # Decode the base64-encoded content
        try:
            file_content = base64.b64decode(file_content_base64)
        except Exception as e:
            return func.HttpResponse(
                body=json.dumps({"error": "Failed to decode base64 content", "details": str(e)}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Save the uploaded file temporarily
        temp_dir = os.getenv('TEMP', '/tmp')
        uploaded_file_path = os.path.join(temp_dir, filename)

        # Write the file to the temporary path
        with open(uploaded_file_path, 'wb') as temp_file:
            temp_file.write(file_content)

        #detect which file should work in 
        pdf_type = detect_pdf_type(uploaded_file_path)

        if pdf_type == "CMR":
            #work on cmr
            page = find_page_with_cmr_data(uploaded_file_path)
            page_dn = find_page_with_cmr_data(uploaded_file_path, keywords=["PRODUCT CODE", "CUSTOMER PART NUMBER", "DESCRIPTION", "u.o.M.", "QUANTITY", "H.U"])
            page_totals = find_page_with_cmr_data(uploaded_file_path, keywords=["DELIVERY NOTE", "TOTAL WEIGHT", "UNITS TOTAL WEIGHT", "PALLETS TOTAL WEIGHT", "VOLUME", "PALLETS"])

            cmr_collis = extract_cmr_collis_data_with_dynamic_coordinates(uploaded_file_path, page_dn[0])
            cmr_adress = extract_text_from_coordinates(uploaded_file_path, cmr_adress_coords, page_dn[0])
            address = get_address_structure(cmr_adress)

            totals = extract_text_from_coordinates(uploaded_file_path, cmr_totals_coords, page_totals[0])

            cmr_data = extract_text_from_coordinates(uploaded_file_path, cmr_coordinates, page_number=page[0])
            cmr_data = handle_cmr_data(cmr_data)

            cmr_data_glb = combine_data_with_material_code(cmr_data, cmr_collis)

        elif pdf_type == "INVOICE":
            #work on the the invoice
            inv_data = extract_text_from_coordinates(uploaded_file_path, invoice_coordinates)
            table_data = extract_table_data_with_dynamic_coordinates(uploaded_file_path)
            table_data = handle_invoice_data(table_data)

        # Delete the temporary uploaded file
        os.remove(uploaded_file_path)

    combined_data = combine_data_with_material_code_collis(cmr_data_glb, table_data)

    body = handle_body_request(email_body)

    #combine the invoice and cmr and body extracted data extra we change inv_data list to json
    json_result = {**list_to_json(inv_data), **body}
    json_result["address"] = address
    json_result["items"] = combined_data

    if totals:
        #add the totals to the json data
        json_result["total pallets"] = totals[0] if totals[0] else ""
        json_result["total weight"] = totals[1] if totals[1] else ""

    #logic here for  exit office and export office and goods location
    if json_result["Exit Port BE"].lower() == "Zeebrugge".lower() :
        json_result["Export office"] = "BEZEE216010"
    else :
        json_result["Export office"] = "BEHSS216000"
        
    # Write the extracted data to an Excel file
    excel_file = write_to_excel(json_result)
    logging.info("Generated Excel file.")

    ref = json_result["Reference"] + "-" + json_result["inv reference"]

    reference = ref if ref else '#No_Ref#'

    # Set response headers for the Excel file download
    headers = {
        'Content-Disposition': 'attachment; filename="' + reference + '.xlsx"',
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }

    try:
        # Return the Excel file as an HTTP response
        return func.HttpResponse(excel_file.getvalue(), headers=headers, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            f"Error processing request: {e}", status_code=500
        )
    
