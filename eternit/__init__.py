import azure.functions as func
import logging
import json

from AI_agents.Gemeni.adress_Parser import AddressParser
from global_db.countries.functions import get_abbreviation_by_country
from eternit.functions.functions import add_pieces_to_hs_and_totals, clean_customs_code, clean_incoterm, clean_number_from_chars, extract_and_clean, extract_customs_code, extract_data, merge_json_objects, normalize_numbers, safe_float_conversion, safe_int_conversion
from eternit.excel.create_excel import write_to_excel

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body.get("files", "")
        email = req_body.get("body", "")

        resutls = []
        
        for file in files :
            documents = file.get("documents")

            result = {}

            for page in documents:
                fields = page["fields"]
                for key, value in fields.items():
                    if key in ["Adress", "Items"]: 
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

            #clean and convert the Gross weight
            gross_weight_total = result.get("Freight", "")
            gross_weight_total = clean_number_from_chars(gross_weight_total)
            if '.' in gross_weight_total or ',' in gross_weight_total:
                gross_weight_total = normalize_numbers(gross_weight_total)
            result["Freight"] = safe_float_conversion(gross_weight_total)
            
            #clean the customs code
            customs_code = result.get("Customs code", "") if result.get("Customs code", "") else ""
            del result["Customs code"]
            result["Customs Code"] = clean_customs_code(customs_code)

            #switch the address country to abbr
            address = result.get("Adress", "")[0]
            parser = AddressParser()
            address = parser.format_address_to_line_old_addresses(address)
            parsed_result = parser.parse_address(address)
            result["Adress"] = parsed_result
            #address["Country"] = get_abbreviation_by_country(address["Country"])

            #clean and split the total value
            total = result.get("Total", "")
            value = normalize_numbers(total)
            value = safe_float_conversion(value)
            total = round(value, 2)
            result["Total"] = total

            #update the numbers in the items
            items = result.get("Items", "")  
            for item in items :
                #handle the value
                Price = item.get("Value", "")
                Price = normalize_numbers(Price)
                Price = safe_float_conversion(Price)
                item["Value"] = Price

                #handle the value
                Gross = item.get("Gross", "")
                Gross = normalize_numbers(Gross)
                Gross = safe_float_conversion(Gross)
                item["Gross"] = Gross

                #handle the value
                Net = item.get("Net", "")
                Net = normalize_numbers(Net)
                Net = safe_float_conversion(Net)
                item["Net"] = Net

                item["Inv Reference"] = result.get("Inv Reference", "")
            
            resutls.append(result)
            
        # Merge JSON objects
        merged_result = merge_json_objects(resutls)
        
        '''------------------   Extract data from the email   ------------------ '''    
        #Extract the body data
        cleaned_email_body_html = extract_and_clean(email)
        
        #extract the table as json object
        email_table = extract_data(cleaned_email_body_html)
        
        merged_result["Exit office"] = email_table.get("Exit office", "").replace("Best", "").strip()
        merged_result["Total pallets"] = email_table.get("collis", 0)
        if email_table.get("freight", ""):
            merged_result["Freight"] = email_table.get("freight", "")[0]
        
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
        
        
  