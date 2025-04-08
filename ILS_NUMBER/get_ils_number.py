import requests
import json

def call_logic_app(principal: str) -> dict:
    """Call Logic App with a PRINCIPAL and return the response."""

    logic_app_url = "https://prod-153.westeurope.logic.azure.com:443/workflows/f757325f47d14b05803514d2ffdb27ff/triggers/When_a_HTTP_request_is_received/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=NqH0ByIRSvt4urzqFgvVPDeGpKHEVnP9PAh0jZeWQcE"  # Replace with your Logic App URL

    payload = {
        "PRINCIPAL": principal
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(logic_app_url, headers=headers, json=payload)
        res.raise_for_status()

        raw_data = res.json()

        # Decode the string inside 'data'
        inner_data = json.loads(raw_data["data"])

        # Extract DOSS_NR
        doss_nr = inner_data["ResultSets"]["Table1"][0]["DOSS_NR"]

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

response = call_logic_app("UMICORE")

if response["success"]:
    print("✅ Got data:", response['doss_nr'])
else:
    print("❌ Error:", response)