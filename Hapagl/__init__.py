import azure.functions as func
import logging
import json

from Hapagl.functions.functions import clean_data, fill_missing_container_values

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        
        result = {}

        documents = req_body["documents"]

        for page in documents:
            fields = page["fields"]
            for key, value in fields.items():
                if key in ["Items"]: 
                    arr = value.get("valueArray")
                    result[key] = []
                    for item in arr:
                        valueObject = item.get("valueObject")
                        obj = {}
                        for keyObj, valueObj in valueObject.items():
                            obj[keyObj] = valueObj.get("valueString", "")
                        result[key].append(obj)          
                else :
                    result[key] = value.get("valueString") 

        result = clean_data(result)
        result = fill_missing_container_values(result)
        
        try:

            return func.HttpResponse(
                json.dumps(result),
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