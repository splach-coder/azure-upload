import azure.functions as func
import logging
import json
from cachetools import TTLCache

from AI_agents.Gemeni.adress_detector_mil_gov import AddressDetector
from RealTimeMilitaryGovernmentGoodsChecker.functions.functions import transform_data

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
            body=json.dumps({"error": "No Data provided"}),
            status_code=400,
            mimetype="application/json"
        )
        
    queryData = data.get("Table1", [])
    data = transform_data(queryData)
   
    detector = AddressDetector()

    for result in data:
        address = result.get("ADDRESS", "")[0]
        parsed_result = detector.parse_address(address)
        result["MIL/GOV"] = parsed_result.replace('\n', '')
    
    try:
        return func.HttpResponse(
            json.dumps(data),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            f"Error processing request: {e}", status_code=500
        )
