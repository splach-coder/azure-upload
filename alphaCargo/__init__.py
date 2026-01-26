import azure.functions as func
import logging
import json
from collections import defaultdict

from alphaCargo.utils import extract_hs_code, merge_invoice_and_pl, fix_hs_codes, detect_missing_fields, repair_with_ai
from alphaCargo.functions.functions import  clean_incoterm, clean_number_from_chars, extract_and_clean, normalize_numbers, safe_float_conversion, safe_int_conversion
from alphaCargo.excel.create_excel import write_to_excel

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    try:
        req_body = req.get_json()
        files = req_body.get("files", {})
        Invs = files.get("Invs", [])
        PLs = files.get("PLs", [])
        email = req_body.get("body", "")

        all_inv_items = []
        all_pl_items = []
        
        Inv_result = {}
        PLs_result = {} 
        
        # Process each invoice file
        for file in Invs:
            documents = file.get("documents", [])
            content = file.get("content", "")
            
            file_result = {}
            file_items = []

            for page in documents:
                fields = page.get("fields", {})
                for key, value in fields.items():
                    if key in ["Items", "Summary"]:
                        arr = value.get("valueArray", [])
                        for item in arr:
                            valueObject = item.get("valueObject", {})
                            obj = {}
                            for keyObj, valObj in valueObject.items():
                                obj[keyObj] = valObj.get("content")    
                            file_items.append(obj)
                            
                    elif key == "Adress":
                        valueObject = value.get("valueObject", {})
                        row1 = valueObject.get("ROW1", {})
                        row1_val_obj = row1.get("valueObject", {})
                        obj = {}
                        for keyObj, valObj in row1_val_obj.items():
                            obj[keyObj] = valObj.get("content")    
                        file_result[key] = [obj]
                    else:
                        file_result[key] = value.get("content")      

            file_result["Items"] = file_items
            logging.error(file_result)
            # AI Fallback for Invoice
            missing = detect_missing_fields(file_result, "Invoice")
            if missing:
                logging.info(f"Missing fields in Invoice: {missing}. Triggering AI fallback.")
                repaired_data = repair_with_ai(content, "Invoice")
                if repaired_data:
                    # If critical item fields are missing, replace list
                    if any(x in missing for x in ["HS CODE", "Quantity", "Amount", "Items"]):
                        logging.info("Replacing items with AI extracted items.")
                        file_result["Items"] = repaired_data.get("Items", file_result.get("Items", []))
                    
                    # Fill missing header fields
                    for key in ["Invoice Number", "Inco Term", "Total Value", "Currency"]:
                        if not file_result.get(key) and repaired_data.get(key):
                            file_result[key] = repaired_data[key]

            # Post-process and normalize
            file_result["Inco Term"] = clean_incoterm(file_result.get("Inco Term", ""))
            
            total_val = str(file_result.get("Total Value", "")).replace(' ', '')
            normalized_total = normalize_numbers(total_val)
            file_result["Total Value"] = round(safe_float_conversion(normalized_total), 2)

            for item in file_result.get("Items", []):
                price = str(item.get("Amount", "")).replace(' ', '')
                item["Amount"] = safe_float_conversion(normalize_numbers(price))
                
                hs_code = item.get("HS CODE") or item.get("Commodity") or ""
                item["HS CODE"] = extract_hs_code(str(hs_code))
                
                qty = item.get("Quantity", "") or item.get("Qty", "")
                item["Qty"] = safe_int_conversion(normalize_numbers(str(qty)))
                item["Invoice Number"] = file_result.get("Invoice Number", "")
                
                
            logging.error(json.dumps(file_result, indent=4))
            # Store results
            Inv_result.update(file_result) # Note: this will keep the last file's header but we accumulate items
            all_inv_items.extend(file_result.get("Items", []))
        
        Inv_result["Items"] = all_inv_items
        
        # Process each packing list file
        for file in PLs:
            documents = file.get("documents", [])
            content = file.get("content", "")

            file_result = {}
            file_items = []

            for page in documents:
                fields = page.get("fields", {})
                for key, value in fields.items():
                    if key in ["Items", "Summary"]:
                        arr = value.get("valueArray", [])
                        for item in arr:
                            valueObject = item.get("valueObject", {})
                            obj = {}
                            for keyObj, valObj in valueObject.items():
                                obj[keyObj] = valObj.get("content")    
                            file_items.append(obj)
                    elif key == "Adress":
                        valueObject = value.get("valueObject", {})
                        row1 = valueObject.get("ROW1", {})
                        row1_val_obj = row1.get("valueObject", {})
                        obj = {}
                        for keyObj, valObj in row1_val_obj.items():
                            obj[keyObj] = valObj.get("content")    
                        file_result[key] = [obj]
                    else:
                        file_result[key] = value.get("content")               

            file_result["Items"] = file_items

            # AI Fallback for PL
            missing = detect_missing_fields(file_result, "Packing List")
            if missing:
                logging.info(f"Missing fields in PL: {missing}. Triggering AI fallback.")
                repaired_data = repair_with_ai(content, "Packing List")
                if repaired_data:
                    if any(x in missing for x in ["Net Weight", "Gross Weight", "Items"]):
                        logging.info("Replacing PL items with AI extracted items.")
                        file_result["Items"] = repaired_data.get("Items", file_result.get("Items", []))
                    
                    for key in ["Total Gross", "Total Net", "Total Packages"]:
                        if not file_result.get(key) and repaired_data.get(key):
                            file_result[key] = repaired_data[key]

            # Normalize PL fields
            for key in ["Total Gross", "Total Net", "Total Packages"]:
                val = clean_number_from_chars(str(file_result.get(key, "")))
                if '.' in val or ',' in val:
                    val = normalize_numbers(val)
                
                if key == "Total Packages":
                    file_result[key] = safe_int_conversion(val)
                else:
                    file_result[key] = safe_float_conversion(val)

            for item in file_result.get("Items", []):
                item["Quantity"] = safe_int_conversion(normalize_numbers(str(item.get("Quantity", ""))))
                item["Ctns"] = safe_int_conversion(normalize_numbers(str(item.get("Ctns", ""))))
                item["Net Weight"] = safe_float_conversion(normalize_numbers(str(item.get("Net Weight", ""))))
                item["Gross Weight"] = safe_float_conversion(normalize_numbers(str(item.get("Gross Weight", ""))))
                item["Invoice Number"] = file_result.get("Invoice Number", "")


            
            PLs_result.update(file_result)
            all_pl_items.extend(file_result.get("Items", []))
        
        PLs_result["Items"] = all_pl_items

        # Fix HS codes and merge
        Inv_result = fix_hs_codes(Inv_result)
        merged_result = merge_invoice_and_pl(Inv_result, PLs_result)
        
        # Email Extraction Fallback
        cleaned_email_body_html = extract_and_clean(email)
        shipping_text = merged_result.get("Origin", "")
        
        from AI_agents.OpenAI.custom_call import CustomCall
        extractor = CustomCall()
        
        prompt = f"""
You are an information extraction engine. Extract ONLY structured data from the following email and shipping text into a single plain JSON object.
- Output ONLY a single plain JSON object. No markdown.
- Numbers must be numeric. Dates must be YYYY-MM-DD.

SCHEMA:
{{
  "Client": {{ "Name": "string", "VAT": "string", "EORI": "string" }},
  "Invoice": {{ "Amount": 0.0, "Currency": "string" }},
  "Shipment": {{
    "Delivery Place": ["Name", "Street + number", "Postcode", "City", "Country Code"],
    "Reference DR": "string", "Client Reference": "string", "ETA": "YYYY-MM-DD",
    "Container Number": "string", "Container Size": "string", "Packages": 0, "Gross Weight": 0.0,
    "Origin Country": "string", "Destination Country": "string"
  }}
}}

EMAIL: {cleaned_email_body_html}
SHIPPING TEXT: {shipping_text}
"""
        email_res = extractor.send_request("System", prompt)
        if email_res:
            email_res = email_res.replace("```json", "").replace("```", "").strip()
            try:
                merged_result["Email"] = json.loads(email_res)
            except:
                merged_result["Email"] = {}
        
        # Generate Excel
        try:
            excel_file = write_to_excel(merged_result)
            
            # Safe reference generation
            email_data = merged_result.get("Email", {})
            shipment = email_data.get("Shipment", {}) if isinstance(email_data, dict) else {}
            ref_dr = shipment.get('Reference DR', 'UNKNOWN') if isinstance(shipment, dict) else 'UNKNOWN'
            container = merged_result.get('Container Number', 'UNKNOWN')
            
            filename = f"{ref_dr}-{container}.xlsx"
            headers = {
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }

            return func.HttpResponse(excel_file.getvalue(), headers=headers, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
        except Exception as e:
            logging.error(f"Excel Generation Error: {e}")
            return func.HttpResponse(f"Error generating excel: {e}", status_code=500)

    except Exception as e:
        logging.error(f"Global Error: {e}")
        return func.HttpResponse(body=json.dumps({"error": str(e)}), status_code=400, mimetype="application/json")
