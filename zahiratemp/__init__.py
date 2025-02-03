import azure.functions as func
import logging
import json
import os
import openpyxl
import base64

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

                # Extract ID from B7
                id_value = sheet['B7'].value

                # Extract invoices array from A24 to A33
                invoices = []
                for row in range(24, 34):  # Rows 24 to 33
                    cell_value = sheet[f'A{row}'].value
                    if cell_value:
                        invoices.append(cell_value)
                    else:
                        break  # Stop if no data is found

                # Extract items array starting from A32, B32, C32, D32
                items = []
                row = 32
                while True:
                    a_value = sheet[f'A{row}'].value
                    b_value = sheet[f'B{row}'].value
                    c_value = sheet[f'C{row}'].value
                    d_value = sheet[f'D{row}'].value

                    if not a_value and not b_value and not c_value and not d_value:
                        break  # Stop if no data is found in the row

                    items.append({
                        'A': a_value,
                        'B': b_value,
                        'C': c_value,
                        'D': d_value
                    })
                    row += 1

                # Create a new Excel file with the extracted data
                new_wb = openpyxl.Workbook()
                new_sheet = new_wb.active

                # Write ID to the new sheet
                new_sheet['A1'] = id_value

                # Write invoices array to the new sheet starting from A24
                for index, invoice in enumerate(invoices, start=3):
                    new_sheet[f'A{index}'] = invoice

                new_sheet['A6'] = 'QTY'
                new_sheet['B6'] = 'Commodity'
                new_sheet['C6'] = 'Origin'
                new_sheet['D6'] = 'Value'

                # Write items array to the new sheet starting from A32
                for index, item in enumerate(items, start=7):
                    new_sheet[f'A{index}'] = item['A']
                    new_sheet[f'B{index}'] = item['B']
                    new_sheet[f'C{index}'] = item['C']
                    new_sheet[f'D{index}'] = item['D']

                # Save the new Excel file in memory
                output_file_path = os.path.join(temp_dir, 'processed_' + filename)
                new_wb.save(output_file_path)

                # Read the processed file for response
                with open(output_file_path, 'rb') as processed_file:
                    file_content = processed_file.read()

                # Delete temporary files
                os.remove(uploaded_file_path)
                os.remove(output_file_path)

                # Set response headers for the Excel file download
                headers = {
                    'Content-Disposition': f'attachment; filename=processed_{filename}',
                    'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                }

                # Return the Excel file as an HTTP response
                return func.HttpResponse(file_content, headers=headers, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

            except Exception as e:
                logging.error(f"Error processing Excel file: {e}")
                return func.HttpResponse(
                    body=json.dumps({"error": f"Failed to process Excel file: {str(e)}"}),
                    status_code=500,
                    mimetype="application/json"
                )

        except Exception as e:
            logging.error(f"Error decoding or saving file: {e}")
            return func.HttpResponse(
                body=json.dumps({"error": f"Failed to decode base64 file: {str(e)}"}),
                status_code=500,
                mimetype="application/json"
            )

    return func.HttpResponse(
        body=json.dumps({"message": "Processing complete."}),
        status_code=200,
        mimetype="application/json"
    )
