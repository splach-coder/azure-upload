import azure.functions as func
import logging
import json

from AI_agents.Gemeni.adress_Parser import AddressParser
from sofidelV2.excel.create_excel import write_to_excel
from global_db.functions.numbers.functions import clean_customs_code, clean_incoterm, clean_number_from_chars, safe_float_conversion, safe_int_conversion
from global_db.countries.functions import get_abbreviation_by_country
from sofidelV2.helpers.functions import arrays_items_collis, arrays_to_objects, extract_id_from_string, transform_data, transform_items_collis
from sofidelV2.utils.functions import handle_body_request, join_cmr_invoice_objects, join_cmrs, join_invoices, join_items
from sofidelV2.utils.number_handlers import normalize_number_format

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body["files"]
        email_body = req_body["body"]
        subject_body = req_body["subject"]
        
        invs = []
        
        for file in files["invs"] :

            #logging.error(json.dumps(file, indent=4))
            documents = file["documents"]
            
            result = {}

            for page in documents:
                fields = page["fields"]
                for key, value in fields.items():
                    if key in ["Address", "Items"]: 
                        arr = value.get("valueArray", [])
                        result[key] = []
                        for item in arr:
                            valueObject = item.get("valueObject")
                            obj = {}
                            for keyObj, valueObj in valueObject.items():
                                obj[keyObj] = valueObj["content"]
                            result[key].append(obj)          
                    else :
                        result[key] = value.get("content")             

            '''------------------   Clean the JSON response   ------------------ '''
            #clean and split the incoterm
            result["Incoterm"] = clean_incoterm(result.get("Incoterm", ""))
            
            #clean the vat
            result["Vat Number"] = result.get("Vat Number", "").replace(".", "")

            #clean the customs code
            customs_code = result.get("Customs code", "") if result.get("Customs code", "") else ""
            result["Customs code"] = clean_customs_code(customs_code)

            #switch the address country to abbr
            address = result.get("Address", "")[0]
            parser = AddressParser()
            address = parser.format_address_to_line_old_addresses(address)
            parsed_result = parser.parse_address(address)
            result["Address"] = parsed_result
            #address["Country"] = get_abbreviation_by_country(address["Country"])

            #clean and split the total value
            total = result.get("Total", "")
            if total:
                value = total
                value = normalize_number_format(value)
                value = safe_float_conversion(value)
                total = value
                result["Total"] = total
            else : 
                result["Total"] = 0.00

            #update the numbers in the items
            items = result.get("Items", "")  
            for item in items :
                item["Pieces"] = safe_int_conversion(item.get("Pieces", 0))
                Price = item.get("Amount", "")
                Price = normalize_number_format(Price)
                Price = safe_float_conversion(Price)
                item["Amount"] = Price            

            invs.append(result)

        cmrs = []

        for file in files["cmrs"] :
            documents = file["documents"]

            result = {}

            for page in documents:
                fields = page["fields"]
                for key, value in fields.items():
                    if key in ["items_collis", "items", "Totals", "Totals_Collis"]: 
                        arr = value.get("valueArray", [])
                        result[key] = []
                        for item in arr:
                            valueObject = item.get("valueObject")
                            obj = {}
                            for keyObj, valueObj in valueObject.items():
                                obj[keyObj] = valueObj["content"]
                            result[key].append(obj)          
                    else :
                        result[key] = value.get("content")                        
                        
                           
            '''------------------   Clean the JSON response   ------------------ '''
            #clean and split the total value
            totals = result.get("Totals", "")
            if totals:
                gross = totals[1].get("values", "")
                gross = clean_number_from_chars(gross)
                gross = normalize_number_format(gross)
                gross = safe_float_conversion(gross)
                result["Gross weight total"] = gross
                
                net = totals[0].get("values", "")
                net = clean_number_from_chars(net)
                net = normalize_number_format(net)
                net = safe_float_conversion(net)
                result["Net weight total"] = net
                
            #clean and split the total value
            totals_collis = result.get("Totals_Collis", "")

            if totals_collis:
                collis = totals_collis[0].get("Pallets", "")
                result["Pallets"] = safe_int_conversion(collis)

            #update the numbers in the items
            items = result.get("items_collis", "")
            tmp_data = transform_items_collis(items)
            tmp_result = arrays_items_collis(tmp_data)
            result["items_collis"] = tmp_result
            for item in tmp_result :
                item["Collis"] = safe_int_conversion(item.get("Collis", 0))       
                
            #update the numbers in the items
            items = result.get("items", "") 
            # Get all keys that appear in any item
            all_keys = set(key for item in items for key in item.keys())

            # Clean the items
            cleaned_items = []
            data_fix_ai = transform_data(items)
            result_fix_ai = arrays_to_objects(data_fix_ai)
            result["items"] = result_fix_ai
            for item in result_fix_ai:
                # Ensure the item has all required keys
                # Process HS code: Keep only the first part of the split
                if 'HS code' in item:
                    item['HS code'] = item['HS code'].split('\n')[0]
                cleaned_items.append(item)
                    
            for item in cleaned_items :  
                item["Pieces"] = safe_int_conversion(item.get("Pieces", 0))
                Price = item.get("Gross Weight", "")
                Price = normalize_number_format(Price)
                Price = safe_float_conversion(Price)
                item["Gross Weight"] = Price
                
            result["items"] = cleaned_items
                
            del result["Totals"]         
            del result["Totals_Collis"]
            
            result = join_items(result)      

            cmrs.append(result)

        inv = join_invoices(invs)
        cmr = join_cmrs(cmrs)
        
        json_result = join_cmr_invoice_objects(inv, cmr)
        
        body = handle_body_request(email_body)

        logging.error(json.dumps(body, indent=4))
        
        json_result = {**json_result, **body}

        json_result["Export office"] = json_result.get("Exit Port BE", "")
        json_result["Exit Port BE"] = ""
        json_result["Reference"] = extract_id_from_string(subject_body)
            
        try:
            # Call writeExcel to generate the Excel file in memory
            excel_file = write_to_excel(json_result)
            logging.info("Generated Excel file.")
            
            reference = f'{json_result.get("Reference", "")}-{json_result.get("Inv Reference", "")}'

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