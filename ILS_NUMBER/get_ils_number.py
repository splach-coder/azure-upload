import logging
import requests
import json

def call_logic_app(principal: str, company = "DKM") -> dict:
    """Call Logic App with a PRINCIPAL and return the response."""

    logic_app_urlDKM = "https://prod-153.westeurope.logic.azure.com:443/workflows/f757325f47d14b05803514d2ffdb27ff/triggers/When_a_HTTP_request_is_received/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=NqH0ByIRSvt4urzqFgvVPDeGpKHEVnP9PAh0jZeWQcE"
    logic_app_urlVP = "https://prod-133.westeurope.logic.azure.com:443/workflows/3183174b4fe94fe7a226f833aebd6dbe/triggers/When_a_HTTP_request_is_received/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=zSvVViH-ONhgH21BwpoUIhWsiwwB2FjhSMzknsa1QBc"
    
    payload = {
        "PRINCIPAL": principal
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        logic_app_url = logic_app_urlVP if company == "vp" else logic_app_urlDKM
        res = requests.post(logic_app_url, headers=headers, json=payload)
        res.raise_for_status()

        raw_data = res.json()

        # Decode the string inside 'data'
        inner_data = json.loads(raw_data["data"])
        
        table1 = inner_data.get("ResultSets", {}).get("Table1", [])

        if not table1:
            doss_nr = 0
        else:
            doss_nr = max(item.get("DOSS_NR", 0) for item in table1)   

        return {
            "success": True,
            "doss_nr": doss_nr
        }
    except requests.exceptions.RequestException as err:
        return {
            "success": False,
            "status_code": getattr(err.response, "status_code", 500),
            "error": str(err)
        }