import azure.functions as func
import logging
import json
import base64
import io  # For in-memory file handling
import openpyxl

from maersk.helpers.functions import  process_container_data
from maersk.helpers.sentEmail import json_to_xml

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing Excel file upload request.')

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

        # Decode the base64-encoded Excel file
        try:
            decoded_data = base64.b64decode(file_data)

            # Load the Excel file into an in-memory BytesIO object
            excel_data = io.BytesIO(decoded_data)
            
            # Load the Excel file using openpyxl
            wb = openpyxl.load_workbook(excel_data)
            sheet = wb.active  # Get the active sheet

            # Initialize variables
            containers = []
            current_container = None
            container_data = {}
        
            # Iterate over rows in the Excel sheet, assuming headers are in the first row
            for row in sheet.iter_rows(min_row=2, values_only=True):
                row = row[:13]
                loyds, stay, vessel_name, container, origin_country, container_packages, net_weight, gross_weight, article_number, bl_number, item, quay, description = row

                if not (loyds and  stay and  vessel_name and  container and  origin_country and  container_packages and  net_weight and  gross_weight and  article_number and  bl_number and  item and  quay and  description) :
                    break
        
                # If we encounter a new container, save the current container data
                if container != current_container:
                    if current_container:
                        containers.append(container_data)
                    
                    # Start new container entry
                    current_container = container
                    container_data = {           
                        "vissel": vessel_name,
                        "container": container,
                        "dispatch_country": origin_country,
                        "Quay": quay,
                        "Stay": stay,
                        "LoydsNumber": loyds,
                        "Article": article_number,
                        "BL number": bl_number,
                        "items": []
                    }
                
                # Add item details to the current container's items
                item_data = {
                    "item": item,
                    "Packages": container_packages,
                    "Net Weight": net_weight,
                    "Gross Weight": gross_weight,
                    "Description": description
                }
                container_data["items"].append(item_data)
        
            # Add the last container
            if container_data:
                containers.append(container_data)

        except Exception as e:
            logging.error(f"Error decoding or processing file: {e}")
            return func.HttpResponse(
                body=json.dumps({"error": f"Failed to decode base64 file: {str(e)}"}),
                status_code=500,
                mimetype="application/json"
            )

    # Process the extracted data if necessary (e.g., further processing or conversion)
    processed_output = process_container_data(containers)

    # Convert the processed output to XML if needed
    xml_data = json_to_xml(processed_output)

    try:
        # Prepare the JSON response
        response = {
            "xml_files": xml_data  # Sending the array of XML strings
        }

        return func.HttpResponse(
            json.dumps(response),
            mimetype="application/json",
            status_code=200
        )
    
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            f"Error processing request: {e}", status_code=500
        )
