import azure.functions as func
import logging
import json

from DailyContainerCheck.functions.functions import is_valid_container_number

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to get the JSON body from the request
    try:
        body = req.get_json()
        data = body.get('data', [])
        
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid request format"}),
            status_code=400,
            mimetype="application/json"
        )

    if not data:
        return func.HttpResponse(
            body=json.dumps({"error": "No files provided"}),
            status_code=400,
            mimetype="application/json"
        )
        
    queryData = data.get("Table1", [])
    
    for row in queryData:
        container = row.get("containerNummer", "")
        if is_valid_container_number(container):
            print(f"{container} is valid.")
        else:
            print(f"{container} is invalid.")
            
            