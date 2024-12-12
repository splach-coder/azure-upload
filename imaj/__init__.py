import azure.functions as func
import logging
import json

from imaj.functions.functions import clean_data_to_structure, create_xml_with_dynamic_values, transform_data, transform_data2
from imaj.data.data import ports

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        
        result = {}

        documents = req_body["body"]["analyzeResult"]["documents"]

        for page in documents:
            fields = page["fields"]
            for key, value in fields.items():
                if key == "Data": 
                    arr = value.get("valueArray")
                    result["data"] = []
                    for item in arr:
                        valueObject = item.get("valueObject")
                        obj = {}
                        for keyObj, valueObj in valueObject.items():
                            obj[keyObj] = valueObj["content"]
                        result["data"].append(obj)          
                else :
                    result[key] = value.get("content")
                    
        extracted_data = transform_data(result)
        cleaned_data = clean_data_to_structure(extracted_data)
        finalversion_data = transform_data2(cleaned_data, ports)
        
        xml_files = {"files" : []}
        
        for file in finalversion_data:
            xml_files["files"].append(create_xml_with_dynamic_values(file))
        
        try:
            return func.HttpResponse(
                json.dumps(xml_files),
                mimetype="application/json",
                status_code=200
            )
    
        except Exception as e:
            logging.error(f"Error: {e}")
            return func.HttpResponse(
                f"Error processing request: {e}", status_code=500
            )              

    except ValueError:
        logging.error("Invalid JSON in request body.")
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json"
        )
        
        
  