import azure.functions as func
import logging
import json

from NCTSv2.functions.functions import fill_items_with_article_parse_numbers, group_data_with_container
from NCTSv2.zip.createzip import write_to_excel

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

        #get country abbr from POL field
        result["POL"] = result.get("POL", "")[0:2]     

        #clean the items data (parse numbers _ append article numbers/bl number)
        result = fill_items_with_article_parse_numbers(result)

        reference = result.get("BLnumber", "")

        #group the data with containers
        results = group_data_with_container(result)
        
        # Proceed with data processing
        try:
            # Generate the ZIP file containing Excel files
            zip_data = write_to_excel(results)
            logging.info("Generated Zip folder.")

            # Return the ZIP file as a response
            return func.HttpResponse(
                zip_data,
                mimetype="application/zip",
                headers={"Content-Disposition": 'attachment; filename="' + reference + '".zip'}
            )

        except TypeError as te:
            logging.error(f"TypeError during processing: {te}")
            return func.HttpResponse(
                body=json.dumps({"error": "Data processing failed due to type error", "details": str(te)}),
                status_code=500,
                mimetype="application/json"
            )

        except Exception as e:
            logging.error(f"Unexpected error during processing: {e}")
            return func.HttpResponse(
                body=json.dumps({"error": "An unexpected error occurred", "details": str(e)}),
                status_code=500,
                mimetype="application/json"
            )             

    except ValueError:
        logging.error("Invalid JSON in request body.")
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json"
        )