import azure.functions as func
import logging
import json
import os
import openpyxl
import base64

from Wynn.helpers.functions import extract_currency_symbol, extract_valid_container, format_float_values, write_to_excel

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to get the JSON body from the request
    try:
        body = req.get_json()
        base64_files = body.get('files', [])
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid request format"}),
            status_code=400,
            mimetype="application/json"
        )

    if not base64_files:
        return func.HttpResponse(
            body=json.dumps({"error": "No files provided"}),
            status_code=400,
            mimetype="application/json"
        )

    for base64_file in base64_files:
        filename = base64_file.get('filename')
        file_data = base64_file.get('file')

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

            # Process the Excel file using openpyxl
            try:
                wb = openpyxl.load_workbook(uploaded_file_path, data_only=True)
                sheet = wb.active  # Get the active sheet

                container = extract_valid_container(sheet.cell(row=26, column=5).value)
                sealNumber = sheet.cell(row=27, column=5).value

                # Extract static values (those not in the items)
                data = {
                    "Goods Validation office": sheet.cell(row=5, column=5).value,  
                    "office of validaton": sheet.cell(row=6, column=5).value,      
                    "Goods Location": sheet.cell(row=7, column=5).value,           
                    "Consignee Name": sheet.cell(row=10, column=5).value,          
                    "Cosnginee street": sheet.cell(row=11, column=5).value,        
                    "consignee city": sheet.cell(row=13, column=5).value + ' ' + sheet.cell(row=12, column=5).value,  
                    "Consignee country": sheet.cell(row=14, column=5).value,       
                    "Reference": sheet.cell(row=16, column=5).value,               
                    "Inco Term": sheet.cell(row=17, column=5).value,               
                    "Inco Term Place": sheet.cell(row=17, column=6).value,         
                    "Exit Office": sheet.cell(row=18, column=5).value,             
                    "e-AD": sheet.cell(row=19, column=4).value,                    
                    "Marks and numbers": sheet.cell(row=20, column=5).value,       
                    "transport identity departure": sheet.cell(row=21, column=5).value,  
                    "transport identity border": sheet.cell(row=22, column=5).value,     
                    "Invoice Value": sheet.cell(row=23, column=5).value,  
                    "Invoice value currency": extract_currency_symbol(sheet.cell(row=23, column=5)),  
                    "Transportmode border": sheet.cell(row=24, column=5).value,    
                    "Transportmode inland": sheet.cell(row=25, column=5).value,    
                    "Freight cost  SEA": sheet.cell(row=24, column=7).value,       
                    "Freight cost ROAD": sheet.cell(row=25, column=7).value,       
                    "Containernumber": container if container != False else "",
                    "Seals": sealNumber if len(sealNumber) > 5 != False else "",
                }

                # Search for the specific header text in the first column to find the start of the table
                header_text = "Factuurnr"  # Replace this with your actual header text
                start_row = None

                # Iterate over the rows to find the header text in the first column
                for row in range(1, sheet.max_row + 1):
                    cell_value = sheet.cell(row=row, column=2).value
                    if cell_value == header_text:
                        start_row = row
                        break
                    
                if start_row is None:
                    raise ValueError("Header text not found in the first column.")

                # Extract the headers from the start_row (assuming the headers are in columns B to P)
                headers = [sheet.cell(row=start_row, column=col).value for col in range(2, 17)]  # Columns B (2) to P (16)

                # Initialize a list to hold the extracted data
                extracted_data = []

                # Counter for consecutive empty rows
                empty_row_count = 0

                # Step 2: Loop through each row after the header
                for row in range(start_row + 1, sheet.max_row + 1):
                    # Extract the data for columns B to P
                    row_data = [sheet.cell(row=row, column=col).value for col in range(2, 17)]

                    # Check if the row is considered empty (first 5 cells are None or empty)
                    if all(cell is None or str(cell).strip() == "" for cell in row_data[:5]):
                        empty_row_count += 1
                    else:
                        empty_row_count = 0  # Reset if a non-empty row is found

                    # Stop processing if 3 or more consecutive empty rows are found
                    if empty_row_count >= 3:
                        break
                    
                    # Create a dictionary (object) for the row if the first 5 cells are not empty
                    if any(cell is not None and str(cell).strip() != "" for cell in row_data[:5]):  # Only check the first 5 cells
                        row_object = {headers[i]: row_data[i] for i in range(len(headers))}
                        extracted_data.append(row_object)

                # Step 3: Print or return the structured dataset
                data["items"] = format_float_values(extracted_data)  # For demonstration, can be modified as needed

            except Exception as e:
                logging.error(f"Error processing Excel file: {e}")
                return func.HttpResponse(
                    body=json.dumps({"error": f"Failed to process Excel file: {str(e)}"}),
                    status_code=500,
                    mimetype="application/json"
                )

            # Delete the temporary uploaded file
            os.remove(uploaded_file_path)

            # Write the extracted data to an Excel file
            excel_file = write_to_excel(data)
            logging.info("Generated Excel file.")

            # Set response headers for the Excel file download
            headers = {
                'Content-Disposition': 'attachment; filename=Reference.xlsx',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }

            # Return the Excel file as an HTTP response
            return func.HttpResponse(excel_file.getvalue(), headers=headers, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        except Exception as e:
            logging.error(f"Error decoding or saving file: {e}")
            return func.HttpResponse(
                body=json.dumps({"error": f"Failed to decode base64 file: {str(e)}"}),
                status_code=500,
                mimetype="application/json"
            )

    
    

    

    
    
    
    
    

    
    
