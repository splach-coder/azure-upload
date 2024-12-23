import azure.functions as func
import logging
import json
import os
import openpyxl
import base64

from bbl.helpers.functions import process_container_data, safe_float_conversion
from bbl.helpers.sentEmail import json_to_xml
from cornelBeechfield.excel.create_excel import write_to_excel
from cornelBeechfield.functions.functions import extract_email_data, process_data

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to get the JSON body from the request
    try:
        body = req.get_json()
        pdfs = body.get('pdf', [])
        excels = body.get('excel', [])
        email = body.get('email', [])
        
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid request format"}),
            status_code=400,
            mimetype="application/json"
        )

    if not pdfs or not excels:
        return func.HttpResponse(
            body=json.dumps({"error": "No files provided"}),
            status_code=400,
            mimetype="application/json"
        )

    extracted_data_from_pdfs = []
    extracted_data_from_excels = []
    
    # Get the data from the excel
    for excel in excels: 
        filename = excel.get('filename')
        file_data = excel.get('file')

        if not filename or not file_data:
            continue

        # Decode the base64-encoded file
        try:
            decoded_data = base64.b64decode(file_data)
            
            temp_dir = os.getenv('TEMP', '/tmp')
            uploaded_file_path = os.path.join(temp_dir, filename)

            # Write the file to the temporary path
            with open(uploaded_file_path, 'wb') as temp_file:
                temp_file.write(decoded_data)
                
            # Load the workbook
            workbook = openpyxl.load_workbook(uploaded_file_path)
            sheet = workbook.active  # Use the first sheet

            # Prepare the output list
            items = []

            # Iterate through rows dynamically
            for row in sheet.iter_rows(min_row=2, values_only=True):  # Assuming the first row is the header
                if all(cell is None for cell in row):  # Stop if the row is completely empty
                    break

                # Safely access the row's values
                despatch_no = row[0]
                commodity_code = row[1]
                description = row[2]
                country_of_origin = row[3]
                qty = row[4]
                cartons = row[5]
                value = row[6]
                currency = row[7]
                net_wt = row[8]
                gross_wt = row[9]

                # Skip rows with critical missing data
                if despatch_no is None or commodity_code is None or description is None:
                    continue

                # Safely convert and handle data types
                item = {
                    "Invoice No": despatch_no if despatch_no else '',
                    "Commodity Code": str(commodity_code) if commodity_code else "",
                    "Description": str(description) if description else "",
                    "Country of Origin": str(country_of_origin) if country_of_origin else "",
                    "Qty": int(qty) if qty else 0,
                    "Cartons": float(cartons) if cartons else 0.00,
                    "Value": float(str(value).replace(',', '')) if value else 0.00,
                    "Currency": str(currency) if currency else "",
                    "Net Wt": float(net_wt) if net_wt else 0.00,
                    "Gross Wt": float(gross_wt) if gross_wt else 0.00
                }
                items.append(item)

            # Output JSON format
            extracted_data_from_excels.append(items)
            
            # Delete the temporary uploaded file
            os.remove(uploaded_file_path)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=4)
    
    for pdf in pdfs:
        documents = pdf.get("documents")
        
        result = {}

        for page in documents:
            fields = page["fields"]
            for key, value in fields.items():
                if key in ["Address", "Items"]: 
                    arr = value.get("valueArray")
                    result[key] = []
                    for item in arr:
                        valueObject = item.get("valueObject")
                        obj = {}
                        for keyObj, valueObj in valueObject.items():
                            obj[keyObj] = valueObj["content"]
                        result[key].append(obj)          
                else :
                    result[key] = value.get("content")
                    
        extracted_data_from_pdfs.append(result)            

    email_data = extract_email_data(email)
    
    logging.error(email_data)

    result_data = {**extracted_data_from_pdfs[0], **email_data,"Items" : extracted_data_from_excels[0]}
    
    result_data = process_data(result_data)

    try:
        # Call writeExcel to generate the Excel file in memory
        excel_file = write_to_excel(result_data)
        logging.info("Generated Excel file.")
        
        reference = result_data.get("Reference", "")

        # Set response headers for the Excel file download
        headers = {
            'Content-Disposition': 'attachment; filename="' + reference + '.xlsx"',
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }

        # Return the Excel file as an HTTP response
        return func.HttpResponse(excel_file.getvalue(), headers=headers, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            f"Error processing request: {e}", status_code=500
        ) 