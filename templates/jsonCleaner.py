import azure.functions as func
import logging
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body["files"]
        email_body = req_body["body"]
        
        
        for file in files:

            #with open('output.json', 'w') as f:
                #json.dump(file, f, indent=4)

            #logging.error(json.dumps(file, indent=4))
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
             
        
        try:
             # Call writeExcel to generate the Excel file in memory
            excel_file = ""
            logging.info("Generated Excel file.")
            
            reference = ""

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
        
        
  