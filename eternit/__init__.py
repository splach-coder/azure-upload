import azure.functions as func
import logging
import json
from collections import defaultdict

from AI_agents.Gemeni.adress_Parser import AddressParser
from ILS_NUMBER.get_ils_number import call_logic_app
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
                    if key in ["Items", "Summary"]:
                        arr = value.get("valueArray")
                        result[key] = []
                        for item in arr:
                            valueObject = item.get("valueObject")
                            obj = {}
                            for keyObj, valueObj in valueObject.items():
                                obj[keyObj] = valueObj["content"]
                            result[key].append(obj)
                            
                    elif key == "Adress":
                        result[key] = []
                        valueObject = value.get("valueObject")
                        arr = valueObject.get("ROW1")
                        valueObject = arr.get("valueObject")
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
                
                #handle the Qty
                Qty = item.get("Qty", "")
                Qty = normalize_numbers(Qty)
                Qty = safe_int_conversion(Qty)
                item["Qty"] = Qty
                
                #handle the Pcs
                Pcs = item.get("Pcs", "")
                Pcs = Pcs.replace(",", "")
                Pcs = safe_int_conversion(Pcs)
                item["Pcs"] = Pcs
                
                #handle the country
                Country = item.get("Origin", "")
                if Country:
                    Country = get_abbreviation_by_country(Country)
                    item["Origin"] = Country

                item["Inv Reference"] = result.get("Inv Reference", "")
            
            merged = defaultdict(lambda: {
                "Qty": 0,
                "Pcs": 0,
                "Inv Reference": "",
                "Origin": ""
            })

            for item in items:
                ct = item['C.T']
                merged[ct]["Qty"] += item.get("Qty", 0)
                merged[ct]["Pcs"] += item.get("Pcs", 0)
                if not merged[ct]["Inv Reference"]:
                    merged[ct]["Inv Reference"] = item.get("Inv Reference", "")
                if not merged[ct]["Origin"]:
                    merged[ct]["Origin"] = item.get("Origin", "")

            # Final output
            merged_list = [
                {
                    "C.T": ct,
                    "Qty": values["Qty"],
                    "Pcs": values["Pcs"],
                    "Inv Reference": values["Inv Reference"],
                    "Origin": values["Origin"]
                }
                for ct, values in merged.items()
            ]
            
            result["Items"] = merged_list
            
            # Convert items to a dict for quick access by C.T
            items_dict = {item['C.T']: item for item in result['Items']}

            # Merge 'Origin' into Summary based on C.T
            for summary in result['Summary']:
                ct = summary['C.T']
                if ct in items_dict:
                    summary['Origin'] = items_dict[ct].get('Origin', '')
                    summary['Qty'] = items_dict[ct].get('Qty', '')
                    summary['Pcs'] = items_dict[ct].get('Pcs', '')
                    summary['Inv Reference'] = items_dict[ct].get('Inv Reference', '')
            
            del result['Items']
            
                        #update the numbers in the items
            summaries = result.get("Summary", "")
            TotalNetWeight = 0
            for summary in summaries :
                #handle the value
                Price = summary.get("Value", "")
                Price = normalize_numbers(Price)
                Price = safe_float_conversion(Price)
                summary["Value"] = Price
                
                #handle the value
                GrossWeight = summary.get("Gross Weight", "")
                GrossWeight = normalize_numbers(GrossWeight)
                GrossWeight = safe_float_conversion(GrossWeight)
                summary["Gross Weight"] = GrossWeight
                
                #handle the value
                NetWeight = summary.get("Net Weight", "")
                NetWeight = normalize_numbers(NetWeight)
                NetWeight = safe_float_conversion(NetWeight)
                TotalNetWeight += NetWeight
                summary["Net Weight"] = NetWeight

            result["Net weight Total"] = TotalNetWeight
            resutls.append(result)
            
        # Merge JSON objects
        merged_result = merge_json_objects(resutls)
        
        logging.error(json.dumps(merged_result, indent=4))     
        
        '''------------------   Extract data from the email   ------------------ '''    
        #Extract the body data
        cleaned_email_body_html = extract_and_clean(email)
        
        #extract the table as json object
        from AI_agents.OpenAI.email_parser import EmailDataExtractor

        extractor = EmailDataExtractor()
        result = extractor.extract_data_from_email(cleaned_email_body_html)
        result = json.loads(result)
        
        merged_result["Exit office"] = result.get("exit_office", "")
        merged_result["Total pallets"] = result.get("collis", 0)
        merged_result["Freight"] = result.get("freight_cost", 0.0)
        
        try:
            # Get the ILS number
            response = call_logic_app("ETERNIT")

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
        
        
  