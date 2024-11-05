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

                # Insert rows above specified indices (12, 16, 20, 24, 28)
                divider_row_indices = [13, 17, 21, 25, 29]
                for index in divider_row_indices:
                    sheet.insert_rows(index)

                # Search and replace "TURKIYE" with "TURKEY" in columns A to D
                for row in sheet.iter_rows(min_row=1, max_row=sheet.max_row, min_col=1, max_col=4):
                    for cell in row:
                        if cell.value == "TURKIYE":
                            cell.value = "TURKEY"

                # Save the changes to a new file in memory
                output_file_path = os.path.join(temp_dir, 'processed_' + filename)
                wb.save(output_file_path)

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
