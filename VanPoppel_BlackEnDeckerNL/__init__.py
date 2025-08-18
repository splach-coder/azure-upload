from ILS_NUMBER.get_ils_number import call_logic_app
import azure.functions as func
import logging
import json
import os
import openpyxl
import base64
import uuid
import re
from decimal import Decimal, InvalidOperation

# --- Assumed Imports based on your request ---
# Make sure these paths are correct in your Azure Function environment.
from AI_agents.Gemeni.adress_Parser import AddressParser
from VanPoppel_BlackEnDeckerNL.excel.create_excel import write_to_excel

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function to extract data from a Stanley Excel file, parse an address,
    and then generate and return a new Excel file.
    """
    logging.info('Processing Stanley Excel data extraction and generation request.')

    # --- 1. Get File from Request ---
    try:
        body = req.get_json()
        excel_file_data = body.get('files', [])[0]
        filename = excel_file_data.get('filename')
        file_content_base64 = excel_file_data.get('file')

        if not filename or not file_content_base64:
            raise ValueError("Request body must contain a 'filename' and 'file' (base64 content).")

    except (ValueError, IndexError, TypeError) as e:
        logging.error(f"Invalid request format: {e}")
        return func.HttpResponse(
            body=json.dumps({"error": f"Invalid request format: {e}"}),
            status_code=400,
            mimetype="application/json"
        )

    # --- 2. Decode and Save Temporary File ---
    temp_file_path = None
    try:
        decoded_data = base64.b64decode(file_content_base64)
        temp_dir = os.getenv('TEMP', '/tmp')
        temp_file_path = os.path.join(temp_dir, filename)
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(decoded_data)
        logging.info(f"Successfully saved temporary file to {temp_file_path}")

    except Exception as e:
        logging.error(f"Error decoding or saving file: {e}")
        return func.HttpResponse(
            body=json.dumps({"error": f"Failed to handle file data: {e}"}),
            status_code=500,
            mimetype="application/json"
        )

    # --- 3. Extract and Process Data ---
    workbook = None
    # --- NEW: Initialize second_layout variable ---
    second_layout = False # Default value
    try:
        workbook = openpyxl.load_workbook(temp_file_path, data_only=True)
        sheet = workbook.active

        def get_cell_value(cell_id):
            cell = sheet[cell_id]
            return cell.value if cell else None
        
        def extract_number(value):
            """Extracts the first integer found in a string."""
            if isinstance(value, str):
                numbers = re.findall(r'\d+', value)
                if numbers:
                    return int(numbers[0])
            if isinstance(value, (int, float)):
                return value
            return None # Return None if no number is found
        
        def get_first_part(value):
            """
            If the value is a string, it splits it by space and returns the first part.
            This safely handles cases with single values, multiple values, or non-string types.
            """
            if isinstance(value, str):
                # .split() handles multiple spaces and returns a list of words
                return value.split()[0]
            # If it's not a string (e.g., a number or None), return it as is
            return value

        # --- NEW: Check for 'bruto' in E13 ---
        e13_value = get_cell_value('E13')
        if isinstance(e13_value, str) and 'bruto' in e13_value.lower():
            second_layout = True
            logging.info(f"Cell E13 contains 'bruto'. Setting second_layout to True.")
        
        # --- Static Data Extraction ---
        header_data = {
            "reference": get_first_part(get_cell_value('B2')),
            "invoice_number": get_first_part(get_cell_value('B3')),
            "delivery_conditions": get_cell_value('B4'),
            "office_of_exit": get_cell_value('B5'),
            "country_of_destination": get_cell_value('B6'),
            "total_amount": get_cell_value('B7'),
            "currency": get_cell_value('B8'),
            "pallet_info": extract_number(get_cell_value('B9')),
            "total_gross_weight_kg": get_cell_value('B10'),
            "total_net_weight_kg": get_cell_value('B11'),
        }

        # --- Corrected Client Data Cells ---
        client_data = {
            "name": get_cell_value('H5'),
            "address": get_cell_value('H6'),
            "postal_code_city": get_cell_value('H7'),
            "country": get_cell_value('H8'),
        }

        # --- Dynamic Line Item Extraction ---
        line_items = []
        for row in sheet.iter_rows(min_row=14, min_col=2, max_col=5, values_only=True):
            hs_code = row[0]
            if hs_code is None:
                break
            try:
                line_items.append({
                    "hs_code": str(hs_code),
                    "amount": float(row[1]) if row[1] is not None else 0.0,
                    "gross_weight_kg": float(row[2]) if row[2] is not None else 0.0,
                    "net_weight_kg": float(row[3]) if row[3] is not None else 0.0,
                })
            except (ValueError, TypeError):
                logging.warning(f"Could not parse numeric data in row with HS Code {hs_code}. Skipping.")
                continue
        
        # --- Address Parsing ---
        address_parts = [client_data['name'], client_data['address'], client_data['postal_code_city'], client_data['country']]
        full_address_string = ", ".join(filter(None, [str(part) for part in address_parts]))
        
        parser = AddressParser()
        parsed_address_list = parser.parse_address(full_address_string)
        
        parsed_address = {
            "company_name": parsed_address_list[0] if len(parsed_address_list) > 0 else None,
            "street": parsed_address_list[1] if len(parsed_address_list) > 1 else None,
            "city": parsed_address_list[2] if len(parsed_address_list) > 2 else None,
            "postal_code": parsed_address_list[3] if len(parsed_address_list) > 3 else None,
            "country_code": parsed_address_list[4] if len(parsed_address_list) > 4 else None,
        }

        # --- Restructure data for write_to_excel function ---
        result_data = {
            "ShipmentReference": header_data.get("reference"),
            "Incoterm": header_data.get("delivery_conditions") + " " + parsed_address.get("city", ""),
            "Total Value": header_data.get("total_amount"),
            "NetWeight": header_data.get("total_net_weight_kg"),
            "GrossWeight": header_data.get("total_gross_weight_kg"),
            "currency": header_data.get("currency"),
            "Collis": header_data.get("pallet_info"),
            "OfficeOfExit": header_data.get("office_of_exit"),
            "PlaceOfDelivery": parsed_address,
            "Invoice No": header_data.get("invoice_number"),
            "Items": line_items 
        }
        logging.info("Successfully extracted and restructured data.")

    except Exception as e:
        logging.error(f"Error during data processing: {e}")
        return func.HttpResponse(
            body=json.dumps({"error": f"Failed to process data: {e}"}),
            status_code=500,
            mimetype="application/json"
        )
    finally:
        if workbook:
            workbook.close()
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logging.info(f"Cleaned up temporary file: {temp_file_path}")
            
    try:
        # Get the ILS number
        response = call_logic_app("STANLEY", company="vp") 

        if response["success"]:
            result_data["ILS_NUMBER"] = response["doss_nr"]
            logging.info(f"ILS_NUMBER: {result_data['ILS_NUMBER']}")
        else:
            logging.error(f"❌ Failed to get ILS_NUMBER: {response['error']}")
    
    except Exception as e:
        logging.exception(f"💥 Unexpected error while fetching ILS_NUMBER: {str(e)}")        

    # --- 4. Generate and Return New Excel File ---
    try:
        logging.error(result_data)
        excel_file_bytes = write_to_excel(result_data)
        logging.info("Generated new Excel file in memory.")
        
        reference = result_data.get("ShipmentReference", "")
        if not reference:
            reference = f"ref-{uuid.uuid4().hex}"

        # --- MODIFIED: Add custom header to the response ---
        headers = {
            'Content-Disposition': f'attachment; filename="{reference}.xlsx"',
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'X-Second-Layout': str(second_layout) # Pass the variable as a string ('True' or 'False')
        }

        return func.HttpResponse(excel_file_bytes.getvalue(), headers=headers)
    
    except Exception as e:
        logging.error(f"Error generating final Excel file: {e}")
        return func.HttpResponse(
            body=f"Error generating response file: {e}", status_code=500
        )