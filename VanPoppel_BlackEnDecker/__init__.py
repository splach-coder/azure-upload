import uuid
import azure.functions as func
import logging
import json
import os
import openpyxl
import base64

from AI_agents.OpenAI.custom_call import CustomCall
from VanPoppel_BlackEnDecker.excel.create_excel import write_to_excel
from VanPoppel_BlackEnDecker.functions.functions import extract_email_body


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to get the JSON body from the request
    try:
        body = req.get_json()
        excels = body.get('files', [])
        email = body.get('email', [])
        subject = body.get('subject', [])
        
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid request format"}),
            status_code=400,
            mimetype="application/json"
        )

    if  not excels:
        return func.HttpResponse(
            body=json.dumps({"error": "No files provided"}),
            status_code=400,
            mimetype="application/json"
        )

    extracted_data_from_excels = []
    TotalPrice = 0
    
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

                # Safely access the row's values with fallback
                BillingDoc = row[0] if len(row) > 0 else None
                Material = row[1] if len(row) > 1 else None
                Description = row[2] if len(row) > 2 else None
                Country_of_origin = row[3] if len(row) > 3 else None
                Qty = row[4] if len(row) > 4 else 0
                TotalCost = row[6] if len(row) > 6 else 0
                Currency = row[7] if len(row) > 7 else ''
                Incoterm = row[8] if len(row) > 8 else ''
                Commodity = row[9] if len(row) > 9 else ''
                Net_wt = row[10] if len(row) > 10 else 0
                Gross_wt = row[13] if len(row) > 13 else 0

                # Skip rows with critical missing data
                if not BillingDoc or not Material or not Description:
                    continue
                
                # Build the item
                item = {
                    "Invoice No": str(BillingDoc),
                    'Incoterm': str(Incoterm),
                    "Material": str(Material),
                    "Commodity Code": str(Commodity),
                    "Description": str(Description),
                    "Country of Origin": str(Country_of_origin),
                    "Qty": int(Qty) if str(Qty).isdigit() else 0,
                    "Total Cost": float(TotalCost) if TotalCost else 0.00,
                    "Value": float(str(TotalCost).replace(',', '')) if TotalCost else 0.00,
                    "Currency": str(Currency),
                    "Net Wt": float(Net_wt) if Net_wt else 0.00,
                    "Gross Wt": float(Gross_wt) if Gross_wt else 0.00
                }
                
                TotalPrice += item["Total Cost"]
            
                items.append(item)

            # Output JSON format
            extracted_data_from_excels.append(items)
            
            # Delete the temporary uploaded file
            os.remove(uploaded_file_path)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=4)
    
    call = CustomCall()
    email = extract_email_body(email)
    role = "you are a data extraction agent. Your task is to extract specific fields from the email text and return them in JSON format. The fields include ShipmentReference, NetWeight, GrossWeight, Incoterm, FreightCost, Collis, OfficeOfExit, and PlaceOfDelivery. If a field is missing, return its value as null. Use number format for numerical values (no units like KG or €). Format 'Incoterm+place name' as a simple lowercase string like 'fca shanghai'."
    prompt = f"""
    Extract the following fields from the email text and return the output as pure JSON with no additional text or formatting. If a field is missing, return its value as null. Use number format for numerical values (no units like KG or €). Format "Incoterm+place name" as a simple lowercase string like "fca shanghai".
    
    Fields to extract:
    - ShipmentReference
    - NetWeight (as number)
    - GrossWeight (as number)
    - Incoterm (as lowercase string, include place name, e.g., "fca marseille")
    - FreightCost (as an object: {{ "value": number, "currency": string }})
    - Collis (as number)
    - OfficeOfExit (as text)
    - PlaceOfDelivery (as object: {{ "company_name": string, "street": string, "city": string, "postal_code": string, "country_code": string (2-letter code) }})
    
    Email text:
    \"\"\"
    {email}
    \"\"\"
    """
    
    email_data = call.send_request(role, prompt)
    email_data = email_data.replace("```", "").replace("json", "").strip()
    
    email = json.loads(email_data)
    
    result_data = {**email, "Total Value" : TotalCost, "Items": extracted_data_from_excels[0]}

    try:
        # Call writeExcel to generate the Excel file in memory
        excel_file = write_to_excel(result_data)
        logging.info("Generated Excel file.")
        
        reference = result_data.get("ShipmentReference", "")
        if not reference:
            reference = f"ref-{uuid.uuid4().hex}"

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