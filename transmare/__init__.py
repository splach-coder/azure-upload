import azure.functions as func
import logging
import json

from global_db.countries.functions import get_abbreviation_by_country
from transmare.functions.functions import  clean_incoterm, clean_Origin, clean_HS_code, clean_number_from_chars, extract_and_clean, extract_Exitoffice, merge_json_objects, normalize_numbers, safe_float_conversion, safe_int_conversion
from transmare.excel.create_excel import write_to_excel

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
                    if key in ["Address", "Items"]: 
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
            
            #clean the VAT number
            result["Vat Number"] = result.get("Vat Number", "").replace(" ", "")
            
            #clean and convert the Gross weight
            gross_weight_total = result.get("Gross weight Total", "")
            gross_weight_total = clean_number_from_chars(gross_weight_total)
            if '.' in gross_weight_total or ',' in gross_weight_total:
                gross_weight_total = normalize_numbers(gross_weight_total)
            result["Gross weight Total"] = safe_float_conversion(gross_weight_total)


            #switch the address country to abbr
            address = result.get("Address", "")[0]
            address["Country"] = get_abbreviation_by_country(address["Country"])

            #clean and split the total value
            total = result.get("Total", "")
            if total:
                total = normalize_numbers(total)
                total = safe_float_conversion(total)
                result["Total"] = total

            #clean and split the total value
            freight = result.get("Freight", "")
            if freight:
                valueF = freight
                valueF = normalize_numbers(valueF)
                valueF = safe_float_conversion(valueF)
                result["Freight"] = valueF

            # Update the numbers in the HSandTotals
            items = result.get("Items", [])
            logging.error(items)
            totalCollis = 0

            # Filter items that have 'Article nbr'
            filtered_items = []
            for item in items:
                if "Article nbr" in item:
                    filtered_items.append(item)
                    for key, value in item.items():
                        if key in ["Net weight", "Price", "Pieces"]:
                            if key == "Pieces":
                                Pieces = safe_int_conversion(item.get(key, 0))
                                item[key] = Pieces
                                totalCollis += Pieces 
                            else:
                                item[key] = normalize_numbers(item.get(key, 0.0))
                                item[key] = safe_float_conversion(item.get(key, 0.0))
                        elif key == "Origin":
                            origin = value     
                            origin = clean_Origin(origin)        
                            item[key] = get_abbreviation_by_country(origin)
                        elif key == "HS code":
                            item[key] = clean_HS_code(item.get(key, ""))

                    item["Inv Reference"] = result.get("Inv Reference", "")  
                else:
                    logging.warning(f"Item removed because 'Article nbr' key is missing: {item}")

            # Update result with filtered items
            result["Items"] = filtered_items
            result["Total pallets"] = totalCollis
            
            resutls.append(result)
            
        # Merge JSON objects
        merged_result = merge_json_objects(resutls)
        
        '''------------------   Extract data from the email   ------------------ '''    
        #Extract the body data
        cleaned_email_body_html = extract_and_clean(email)
        
        #Extract the body data
        merged_result["Exit office"] = extract_Exitoffice(cleaned_email_body_html)
        
        try:
            # Call writeExcel to generate the Excel file in memory
            excel_file = write_to_excel(merged_result)
            logging.info("Generated Excel file.")
            
            reference = merged_result.get("Inv Reference", "")

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
        
        
  