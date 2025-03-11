import azure.functions as func
import logging
import json

from AI_agents.Gemeni.adress_Parser import AddressParser
from AI_agents.Gemeni.functions.functions import convert_to_list
from AI_agents.Gemeni.transmare_Email import TransmareEmailParser
from global_db.countries.functions import get_abbreviation_by_country
from global_db.functions.dates import change_date_format
from FMinvoices.functions.functions import  clean_incoterm, clean_Origin, clean_HS_code, clean_number_from_chars, extract_and_clean, extract_Exitoffice, merge_json_objects, normalize_numbers, normalize_numbers_gross, safe_float_conversion, safe_int_conversion
from FMinvoices.excel.create_excel import write_to_excel
from global_db.functions.container import is_valid_container_number, is_valid_quay_number

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body["files"]
        
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
            result["Vat Number"] = result.get("Vat number", "").replace(" ", "")
            
            #clean and convert the Gross weight
            gross_weight_total = result.get("Total Gross", "")
            gross_weight_total = clean_number_from_chars(gross_weight_total)
            if '.' in gross_weight_total or ',' in gross_weight_total:
                gross_weight_total = normalize_numbers(gross_weight_total)
            result["Total Gross"] = safe_float_conversion(gross_weight_total)

            #clean and convert the Total Net
            gross_weight_total = result.get("Total Net", "")
            gross_weight_total = clean_number_from_chars(gross_weight_total)
            if '.' in gross_weight_total or ',' in gross_weight_total:
                gross_weight_total = normalize_numbers(gross_weight_total)
            result["Total Net"] = safe_float_conversion(gross_weight_total)

            #clean and convert the Total Price
            gross_weight_total = result.get("Total Price", "")
            gross_weight_total = clean_number_from_chars(gross_weight_total)
            if '.' in gross_weight_total or ',' in gross_weight_total:
                gross_weight_total = normalize_numbers(gross_weight_total)
            result["Total Price"] = safe_float_conversion(gross_weight_total)

            #clean and convert the Total Collis
            gross_weight_total = result.get("Total Collis", "")
            gross_weight_total = clean_number_from_chars(gross_weight_total)
            if '.' in gross_weight_total or ',' in gross_weight_total:
                gross_weight_total = normalize_numbers(gross_weight_total)
            result["Total Collis"] = safe_int_conversion(gross_weight_total)

            #switch the address country to abbr
            address = result.get("Address", "")[0]
            parser = AddressParser()
            address = parser.format_address_to_line_old_addresses(address)
            parsed_result = parser.parse_address(address)
            result["Address"] = parsed_result

            # Update the numbers in the HSandTotals
            items = result.get("Items", [])

            # Filter items that have 'Article nbr'
            filtered_items = []
            for item in items:
                if "Material" in item:
                    filtered_items.append(item)
                    for key, value in item.items():
                        if key in ["Price", "Collis"]:
                            if key == "Collis":
                                Pieces = safe_int_conversion(item.get(key, 0))
                                item[key] = Pieces
                            else:    
                                number_value = item.get(key, 0.0)
                                item[key] = normalize_numbers(number_value)
                                item[key] = safe_float_conversion(item.get(key, 0.0))
                        elif key == "HS":
                            item[key] = clean_HS_code(item.get(key, ""))

                    item["Inv Reference"] = result.get("Inv Ref", "")  
                else:
                    logging.warning(f"Item removed because 'Article nbr' key is missing: {item}")

            # Update result with filtered items
            result["Items"] = filtered_items
            
            resutls.append(result)

        # Change to Date
        for inv in resutls:  
            prev_date = inv.get('Inv Date', '')
            new_date = change_date_format(prev_date)
            inv["Inv Date"] = new_date

                
            
        # Merge JSON objects
        merged_result = merge_json_objects(resutls)
        logging.error(merged_result)

        
        try:
            # Call writeExcel to generate the Excel file in memory
            excel_file = write_to_excel(merged_result)
            logging.info("Generated Excel file.")
            
            reference = merged_result.get("Inv Ref", "")

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
        
        
  