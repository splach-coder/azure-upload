import azure.functions as func
import logging
import json

from global_db.countries.functions import get_abbreviation_by_country
from eternit.functions.functions import add_pieces_to_hs_and_totals, clean_customs_code, clean_incoterm, clean_number_from_chars, extract_and_clean, extract_customs_code, extract_data, merge_json_objects, normalize_numbers, safe_float_conversion, safe_int_conversion
from eternit.excel.create_excel import write_to_excel

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body["files"]
        email = req_body["body"]
        
        resutls = []
        
        for file in files :
            documents = file["documents"]

            result = {}

            for page in documents:
                fields = page["fields"]
                for key, value in fields.items():
                    if key in ["Address", "Items", "HSandTotals"]: 
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

            '''------------------   Clean the JSON response   ------------------ '''
            
            #clean and split the incoterm
            result["Incoterm"] = clean_incoterm(result.get("Incoterm", ""))
            
            
            #clean and convert the Gross weight
            gross_weight_total = result.get("Gross weight Total", "")
            gross_weight_total = clean_number_from_chars(gross_weight_total)
            if '.' in gross_weight_total or ',' in gross_weight_total:
                gross_weight_total = normalize_numbers(gross_weight_total)
            result["Gross weight Total"] = safe_float_conversion(gross_weight_total)
            
            #clean the customs code
            customs_code = result.get("Customs Code", "") if result.get("Customs Code", "") else ""
            result["Customs Code"] = clean_customs_code(customs_code)

            #switch the origin country to abbr
            origin_country = result.get("Origin Country", "") if result.get("Origin Country", "") else ""
            result["Origin Country"] = get_abbreviation_by_country(origin_country)

            #switch the address country to abbr
            address = result.get("Address", "")[0]
            address["Country"] = get_abbreviation_by_country(address["Country"])

            #clean and split the total value
            total = result.get("Total", "").split(' ', maxsplit=1)
            if(len(total) > 1):
                value, currency = total
                value = normalize_numbers(value)
                value = safe_float_conversion(value)
                total = [round(value, 2), currency]
                logging.error(total)
                result["Total"] = total
            else : 
                total = [0.00, ""]

            #update the numbers in the items
            items = result.get("Items", "")  
            for item in items :
                item["Pieces"] = safe_int_conversion(item.get("Pieces", ""))
                Price = item.get("Price", "")
                Price = normalize_numbers(Price)
                Price = safe_float_conversion(Price)
                item["Price"] = Price 
            
            #update items with HS code based on TVA CT and CA match
            items = result.get("Items", "")
            hs_and_totals = result.get("HSandTotals")
            result["HSandTotals"] = add_pieces_to_hs_and_totals(items, hs_and_totals)

            #update the numbers in the HSandTotals
            items = result.get("HSandTotals", "")  
            for item in items :
                if not item.get("Net Value", "") and item["HS code"] == "Z0000000":
                    items.remove(item)

                for key, value in item.items():
                    if key in ["Gross Weight", "Net weight", "Net Value"]:
                        item[key] = normalize_numbers(item.get(key, 0.0))
                        item[key] = safe_float_conversion(item.get(key, 0.0))
                    elif key == "Origin" :
                        if not item[key]:
                            if result.get("Origin Country", ""):
                                item[key] = result.get("Origin Country", "")
                            else :
                                item[key] = ""
                        else :
                            item[key] = get_abbreviation_by_country(value)        
                
                item["Inv Reference"] = result.get("Inv Reference", "")  
                item["Customs Code"] = result.get("Customs Code", "")  

            del result["Items"]
            
            

            resutls.append(result)
            
        # Merge JSON objects
        merged_result = merge_json_objects(resutls)
        
        '''------------------   Extract data from the email   ------------------ '''    
        #Extract the body data
        cleaned_email_body_html = extract_and_clean(email)
        
        #extract the table as json object
        email_table = extract_data(cleaned_email_body_html)
        
        merged_result["Exit office"] = email_table.get("Exit office", "")
        merged_result["Total pallets"] = email_table.get("collis", "")
        #clean and split the total value
        freight = email_table.get("freight", "")
        if(len(freight) > 1):
            valueF, currencyF = freight
            freight = [valueF, currencyF.upper()]
            merged_result["Freight"] = freight
        else : 
            merged_result["Freight"] = [0.00, ""]
            
        logging.error(json.dumps(merged_result, indent=4))    
        
        try:
            # Call writeExcel to generate the Excel file in memory
            excel_file = write_to_excel(merged_result)
            logging.info("Generated Excel file.")
            
            reference = merged_result.get("Bon de livraison", "")

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
        
        
  