import azure.functions as func
import logging
import json

from DailyContainerCheck.functions.functions import is_valid_container_number, string_to_unique_array

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
    data = []
    wrong_data = [] 
    
    for row in queryData:
        containers = row.get("CONTAINERS", "")
        containers = string_to_unique_array(containers)
        
        data.append({
            "CONTAINERS": containers,
            "DECLARATIONID" : row.get("DECLARATIONID", ""),
            "DATEOFACCEPTANCE" : row.get("DATEOFACCEPTANCE", ""),
            "TYPEDECLARATIONSSW" : row.get("TYPEDECLARATIONSSW", ""),
            "ACTIVECOMPANY" : row.get("ACTIVECOMPANY", ""),
            "USERCREATE" : row.get("USERCREATE", "")
        })

    for obj in data:
        containers = obj.get("CONTAINERS", "")
        newObj = {**obj}
        newObj["CONTAINERS"] = []
        for container in containers:
            continernumberLength = len(container)
            if continernumberLength == 11 or continernumberLength == 17:
                if len(container) == 11:
                    if not is_valid_container_number(container):
                        newObj["CONTAINERS"].append(container)
                        wrong_data.append(newObj)
            else:
                newObj["CONTAINERS"].append(container)
                wrong_data.append(newObj)

    try:
        return func.HttpResponse(
            json.dumps(wrong_data),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            f"Error processing request: {e}", status_code=500
        )