import azure.functions as func
import logging
import json
from collections import defaultdict

from alphaCargo.utils import extract_hs_code, merge_invoice_and_pl, fix_hs_codes
from alphaCargo.functions.functions import  clean_incoterm, clean_number_from_chars, extract_and_clean, normalize_numbers, safe_float_conversion, safe_int_conversion
from alphaCargo.excel.create_excel import write_to_excel

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body.get("files", "")
        Invs = files.get("Invs", "")
        PLs = files.get("PLs", "")
        email = req_body.get("body", "")

        Inv_result = {}
        PLs_result = {} 
        
        # Process each invoice file
        for file in Invs :
            documents = file.get("documents")

            result = {}

            for page in documents:
                fields = page.get("fields")
                for key, value in fields.items():
                    if key in ["Items", "Summary"]:
                        arr = value.get("valueArray")
                        result[key] = []
                        for item in arr:
                            valueObject = item.get("valueObject")
                            obj = {}
                            for keyObj, valueObj in valueObject.items():
                                obj[keyObj] = valueObj.get("content")    
                            result[key].append(obj)
                            
                    elif key == "Adress":
                        result[key] = []
                        valueObject = value.get("valueObject")
                        arr = valueObject.get("ROW1")
                        valueObject = arr.get("valueObject")
                        obj = {}
                        for keyObj, valueObj in valueObject.items():
                            obj[keyObj] = valueObj.get("content")    
                        result[key].append(obj)
                    else :
                        result[key] = value.get("content")      

            '''------------------   Clean the JSON response   ------------------ '''       
            #clean and split the incoterm
            result["Inco Term"] = clean_incoterm(result.get("Inco Term", ""))

            #clean and split the total value
            total = result.get("Total Value", "")
            total = total.replace(' ', '')
            value = normalize_numbers(total)
            value = safe_float_conversion(total)
            total = round(value, 2)
            result["Total Value"] = total

            #update the numbers in the items
            items = result.get("Items", "")  
            for item in items :
                #handle the value
                Price = item.get("Amount", "")
                if Price is not None:
                    Price = Price.replace(' ', '')
                    Price = normalize_numbers(Price)
                    Price = safe_float_conversion(Price)
                    item["Amount"] = Price
                
                HsCode = item.get("HS CODE", "")
                HsCode = extract_hs_code(HsCode)
                item["HS CODE"] = HsCode
                
                #handle the Qty
                Qty = item.get("Quantity", "")
                Qty = normalize_numbers(Qty)
                Qty = safe_int_conversion(Qty)
                item["Qty"] = Qty

                item["Invoice Number"] = result.get("Invoice Number", "")
            
            Inv_result = result
        
        # Parse each packing list file
        for file in PLs :
            documents = file.get("documents")

            result = {}

            for page in documents:
                fields = page.get("fields")
                for key, value in fields.items():
                    if key in ["Items", "Summary"]:
                        arr = value.get("valueArray")
                        result[key] = []
                        for item in arr:
                            valueObject = item.get("valueObject")
                            obj = {}
                            for keyObj, valueObj in valueObject.items():
                                obj[keyObj] = valueObj.get("content")    
                            result[key].append(obj)
                            
                    elif key == "Adress":
                        result[key] = []
                        valueObject = value.get("valueObject")
                        arr = valueObject.get("ROW1")
                        valueObject = arr.get("valueObject")
                        obj = {}
                        for keyObj, valueObj in valueObject.items():
                            obj[keyObj] = valueObj.get("content")    
                        result[key].append(obj)
                    else :
                        result[key] = value.get("content")               

            '''------------------   Clean the JSON response   ------------------ '''                   
            #clean and convert the Gross weight
            gross_weight_total = result.get("Total Gross", "")
            gross_weight_total = clean_number_from_chars(gross_weight_total)
            if '.' in gross_weight_total or ',' in gross_weight_total:
                gross_weight_total = normalize_numbers(gross_weight_total)
            result["Total Gross"] = safe_float_conversion(gross_weight_total)
            
            #clean and convert the Net weight
            gross_weight_total = result.get("Total Packages", "")
            gross_weight_total = clean_number_from_chars(gross_weight_total)
            if '.' in gross_weight_total or ',' in gross_weight_total:
                gross_weight_total = normalize_numbers(gross_weight_total)
            result["Total Packages"] = safe_int_conversion(gross_weight_total)
            
            #clean and convert the Gross weight
            gross_weight_total = result.get("Total Net", "")
            gross_weight_total = clean_number_from_chars(gross_weight_total)
            if '.' in gross_weight_total or ',' in gross_weight_total:
                gross_weight_total = normalize_numbers(gross_weight_total)
            result["Total Net"] = safe_float_conversion(gross_weight_total)

            #update the numbers in the items
            items = result.get("Items", "")  
            for item in items :
                #handle the value
                Qty = item.get("Quantity", "")
                Qty = normalize_numbers(Qty)
                Qty = safe_int_conversion(Qty)
                item["Quantity"] = Qty
                
                Ctns = item.get("Ctns", "")
                Ctns = normalize_numbers(Ctns)
                Ctns = safe_int_conversion(Ctns)
                item["Ctns"] = Ctns
                
                Net = item.get("Net Weight", "")
                Net = normalize_numbers(Net)
                Net = safe_float_conversion(Net)
                item["Net Weight"] = Net
                
                Net = item.get("Gross Weight", "")
                Net = normalize_numbers(Net)
                Net = safe_float_conversion(Net)
                item["Gross Weight"] = Net

                item["Invoice Number"] = result.get("Invoice Number", "")
            
            PLs_result = result
        
        # Fix HS codes in the invoice items
        Inv_result = fix_hs_codes(Inv_result)
        
        # Merge JSON objects
        merged_result = merge_invoice_and_pl(Inv_result, PLs_result)
        
        '''------------------   Extract data from the email   ------------------ '''    
        #Extract the body data
        cleaned_email_body_html = extract_and_clean(email)
        shipping_text = merged_result.get("Origin", "")
        
        #extract the table as json object
        from AI_agents.OpenAI.custom_call import CustomCall

        extractor = CustomCall()
        prompt = f"""
You are an information extraction engine.
Extract ONLY structured data from the following email and shipping text into a single plain JSON object.

Constraints:
- Output ONLY a single plain JSON object. No markdown, no backticks, no explanation, no extra text.
- If a field is missing, omit it (do not invent values).
- Numbers must be JSON numbers (no quotes). Use dot as decimal separator (e.g. 17959.5).
- Dates must be ISO format: YYYY-MM-DD.
- Keys must match the schema below (use as a guide). Use real values from the email and shipping text.

SCHEMA:
{{
  "Client": {{
    "Name": "string",
    "VAT": "string",
    "EORI": "string"
  }},
  "Invoice": {{
    "Amount": 0.0,
    "Currency": "string"
  }},
  "Shipment": {{
    "Delivery Place": [
      "Name",
      "Street + number",
      "Postcode",
      "City",
      "Country" As country code (e.g. NL, DE, BE)
    ],
    "Reference DR": "string",
    "Client Reference": "string",
    "ETA": "YYYY-MM-DD",
    "Container Number": "string",
    "Container Size": "string",
    "Packages": 0,
    "Gross Weight": 0.0,
    "Origin Country": "string", as country code (e.g. NL, DE, BE)
    "Destination Country": "string" as country code (e.g. NL, DE, BE)
  }}
}}

Now extract the JSON from the following inputs.  
EMAIL:  
{cleaned_email_body_html}  

SHIPPING TEXT:  
{shipping_text}
""" 

        role = "System"

        result = extractor.send_request(role, prompt)
        result = result.replace("```", "").replace("json", "").strip()
        result = json.loads(result)
        
        merged_result["Email"] = result
        
        try:
            # Call writeExcel to generate the Excel file in memory
            excel_file = write_to_excel(merged_result)
            logging.info("Generated Excel file.")
            
            reference = f"{merged_result.get('Email', '').get('Shipment', '').get('Reference DR', '')}-{merged_result.get('Container Number', '')}"

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

    except ValueError as e:
        logging.error("Invalid JSON in request body.")
        logging.error(e)
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json"
        )