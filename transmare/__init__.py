import uuid
import azure.functions as func
import logging
import json

from AI_agents.Gemeni.adress_Parser import AddressParser
from AI_agents.Gemeni.functions.functions import convert_to_list
from AI_agents.Gemeni.transmare_Email import TransmareEmailParser
from ILS_NUMBER.get_ils_number import call_logic_app
from global_db.countries.functions import get_abbreviation_by_country
from global_db.functions.dates import change_date_format
from transmare.functions.functions import  clean_incoterm, clean_Origin, clean_HS_code, clean_number_from_chars, extract_and_clean, extract_Exitoffice, merge_json_objects, normalize_numbers, normalize_numbers_gross, safe_float_conversion, safe_int_conversion
from transmare.excel.create_excel import write_to_excel
from global_db.functions.container import is_valid_container_number, is_valid_quay_number



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
            parser = AddressParser()
            address = parser.format_address_to_line_old_addresses(address)
            parsed_result = parser.parse_address(address)
            result["Address"] = parsed_result

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
            totalCollis = 0
            totalNet = 0

            # Filter items that have 'Article nbr'
            filtered_items = []
            for item in items:
                if "Article nbr" in item:
                    filtered_items.append(item)
                    for key, value in item.items():
                        if key in ["Net weight", "Gross weight", "Price", "Pieces"]:
                            if key == "Pieces":
                                Pieces = safe_int_conversion(item.get(key, 0))
                                item[key] = Pieces
                                totalCollis += Pieces 
                            elif key == "Gross weight" :
                                number_value = item.get(key, 0.0)
                                number_value = normalize_numbers_gross(number_value)
                                item[key] = safe_float_conversion(number_value)
                            else:    
                                number_value = item.get(key, 0.0)
                                item[key] = normalize_numbers(number_value)
                                if len(item[key]) == 0:
                                    item[key] = safe_int_conversion(number_value)
                                item[key] = safe_float_conversion(item.get(key, 0.0))
                                if key == "Net weight" :
                                    totalNet += item.get(key, 0)
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
            result["Total net"] = totalNet
            
            resutls.append(result)
            
        # Merge JSON objects
        merged_result = merge_json_objects(resutls)
        
        '''------------------   Extract data from the email   ------------------ '''    
        #Extract the body data
        cleaned_email_body_html = extract_and_clean(email)
        
        #Extract the body data
        # inv = merged_result.get("Inv Reference", "") if merged_result.get("Inv Reference") is not None else ""
        # merged_result["Exit office"] = extract_Exitoffice(cleaned_email_body_html.replace(inv ,''))

        parser = TransmareEmailParser()
        parsed_result = parser.parse_email(cleaned_email_body_html)
        parsed_result = parsed_result.replace('json', '').replace('```', '').strip()
        parsed_result = convert_to_list(parsed_result)
        merged_result["Vissel"] = parsed_result.get("Vissel name")
        merged_result["Exit office"] = parsed_result.get("Exit office").replace(" ", "") if parsed_result.get("Exit office") else ""
        merged_result["kaai"] = parsed_result.get("Export kaai", "") if is_valid_quay_number(parsed_result.get("Export kaai", "")) else ""
        merged_result["Container"] = parsed_result.get("Container Number", "") if is_valid_container_number(parsed_result.get("Container Number", "")) else ""
        merged_result["Email"] = parsed_result.get("Email", "")

        prev_date = merged_result.get('Inv Date', '')
        new_date = change_date_format(prev_date)
        merged_result["Inv Date"] = new_date
        
        try:
            # Get the ILS number
            response = call_logic_app("TRANSMA")

            if response["success"]:
                merged_result["ILS_NUMBER"] = response["doss_nr"]
                logging.info(f"ILS_NUMBER: {merged_result['ILS_NUMBER']}")
            else:
                logging.error(f"❌ Failed to get ILS_NUMBER: {response['error']}")
    
        except Exception as e:
            logging.exception(f"💥 Unexpected error while fetching ILS_NUMBER: {str(e)}")
        
        try:
            # Call writeExcel to generate the Excel file in memory
            excel_file = write_to_excel(merged_result)
            logging.info("Generated Excel file.")
            
            reference = merged_result.get("Inv Reference", "") or ("transmare_" + uuid.uuid4().hex[:8])

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
        
        
  