import azure.functions as func
import logging
import json
from cachetools import TTLCache

from DailyContainerCheck.functions.functions import is_valid_container_number, string_to_unique_array

# Initialize the TTLCache with a maximum size and time-to-live (TTL)
error_cache = TTLCache(maxsize=2000, ttl=86400000)  # Cache stores up to 2000 items for 1 day (86400 seconds)

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
            "DECLARATIONID": row.get("DECLARATIONID", ""),
            "DATEOFACCEPTANCE": row.get("DATEOFACCEPTANCE", ""),
            "TYPEDECLARATIONSSW": row.get("TYPEDECLARATIONSSW", ""),
            "ACTIVECOMPANY": row.get("ACTIVECOMPANY", ""),
            "USERCREATE": row.get("USERCREATE", "")
        })

    for obj in data:
        containers = obj.get("CONTAINERS", "")
        newObj = {**obj}
        newObj["CONTAINERS"] = []
        for container in containers:
            container_number_length = len(container)
            # If container length is valid, check further
            if container_number_length != 0:
                if container_number_length == 11 or container_number_length == 17:
                    if container_number_length == 11:
                        # Check container validity
                        if not is_valid_container_number(container):
                            if container not in error_cache:
                                # Add container to cache
                                error_cache[container] = newObj
                                newObj["CONTAINERS"].append(container)
                                wrong_data.append(newObj)
                else:
                    # Invalid length containers
                    if container not in error_cache:
                        error_cache[container] = newObj
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
