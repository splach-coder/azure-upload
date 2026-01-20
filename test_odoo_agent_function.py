import requests
import json

# Test the OdooProjectAgent Azure Function locally
url = "http://localhost:7073/api/OdooProjectAgent"

# Sample email from Luc
payload = {
    "email_body": """
    Hi Team,
    
    We need to set up a new flow for ACME Corporation.
    
    They will be sending invoices as PDF attachments via email.
    The subject line will contain the invoice reference number.
    
    We need to:
    - Extract data using Azure AI Document Intelligence
    - Process it through Logic App 'la-acme-invoice-processor'
    - Use an Azure Function for validation
    - Output should be Excel format
    
    Please set this up ASAP.
    
    Thanks,
    Luc
    """,
    "subject": "New Project: ACME Invoice Processing",
    "attachments": ["invoice_001.pdf", "invoice_002.pdf"]
}

print("Sending request to OdooProjectAgent...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\n" + "="*50 + "\n")

try:
    response = requests.post(url, json=payload, timeout=60)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        print("\n✅ SUCCESS: Odoo project created!")
    else:
        print("\n❌ FAILED: Check the error details above")
        
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Could not connect to Azure Functions.")
    print("Make sure 'func start' is running on port 7073")
except Exception as e:
    print(f"❌ ERROR: {e}")
