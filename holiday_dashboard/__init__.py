import azure.functions as func
import msal
import requests
import json

# 🔹 Your Microsoft Account Email
USER_EMAIL = "anas.benabbou@dkm-customs.com"

# 🔹 Microsoft Authentication (Interactive)
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["https://graph.microsoft.com/.default"]

# 🔹 SharePoint Details
SITE_URL = "https://dkmcustoms.sharepoint.com/sites/DKMMARRAKECHAutomatedHolidayManagementSystem"
LIST_NAME = "Employee Balance"

def get_sharepoint_data():
    """Authenticate and fetch SharePoint list data"""
    app = msal.PublicClientApplication(client_id="d3590ed6-52b3-4102-aeff-aad2292ab01c", authority=AUTHORITY)
    
    # Get Access Token (Manual Login Required)
    token = app.acquire_token_interactive(SCOPES)
    
    if "access_token" in token:
        access_token = token["access_token"]
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        # SharePoint API URL
        api_url = f"{SITE_URL}/_api/web/lists/getbytitle('{LIST_NAME}')/items"
        
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to fetch data: {response.status_code}"}
    
    return {"error": "Authentication failed"}

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Function entry point"""
    try:
        data = get_sharepoint_data()
        return func.HttpResponse(json.dumps(data), mimetype="application/json", status_code=200)
    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
