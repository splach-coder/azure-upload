import requests
import json
import time

# Test the StoreProjectOnOdoo Azure Function locally
# Note: Ensure 'func start' is running
url = "http://localhost:7071/api/StoreProjectOnOdoo"

# Sample email from Luc
payload = {
    "subject": "VanPoppel - Invoice Automation",
    "from": "luc@vanpoppel.com",
    "to": "projects@dkm.com",
    "body": """
    Hi team,
    
    We need to automate invoice processing for VanPoppel.
    They send PDFs via email.
    We need to extract the data and push to Odoo.
    
    Urgent request.
    
    Thanks,
    Luc
    """,
    "receivedDateTime": "2026-01-21T12:00:00Z",
    "importance": "high",
    "attachments": [
        {
            "name": "invoice_sample.pdf", 
            "contentType": "application/pdf",
            # Minimal PDF base64 for testing
            "contentBytes": "JVBERi0xLjcKCjEgMCBvYmogICUgZW50cnkgcG9pbnQKPDwKICAvVHlwZSAvQ2F0YWxvZwogIC9QYWdlcyAyIDAgUgo+PgplbmRvYmoKCjIgMCBvYmogCjw8CiAgL1R5cGUgL1BhZ2VzCiAgL01lZGlhQm94IFsgMCAwIDIwMCAyMDAgXQogIC9Db3VudCAxCiAgL0tpZHMgWyAzIDAgUiBdCj4+CmVuZG9iagoKQ29udGVudHMKPDwKICAvTGVuZ3RoIDQ0Cj4+CnN0cmVhbQpxCjEwIDAgMCAxMCAxMCAxMCBjbQpCVCAvRjEgMTIgVGYgKHelloIFdvcmxkKSBUaiBFVApRCmVuZHN0cmVhbQplbmRvYmoKCjMgMCBvYmoKPDwKICAvVHlwZSAvUGFnZQogIC9QYXJlbnQgMiAwIFIKICAvUmVzb3VyY2VzIDw8CiAgICAvRm9udCA8PAogICAgICAvRjEgPDwKICAgICAgICAvVHlwZSAvRm9udAogICAgICAgIC9TdWJ0eXBlIC9UeXBlMQogICAgICAgIC9CYXNlRm9udCAvSGVsdmV0aWNhCiAgICAgID4+CiAgICA+PgogID4+CiAgL0NvbnRlbnRzIDIgMCBSCj4+CmVuZG9iagoKeHJlZgowIDQKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDEwIDAwMDAwIG4gCjAwMDAwMDAwNjAgMDAwMDAgbiAKMDAwMDAwMDIzNSAwMDAwMCBuIAp0cmFpbGVyCjw8CiAgL0N1c3RvbSA8PAogICAgL0FwcCAnVGVzdCcKICA+PgogIC9TaXplIDQKICAvUm9vdCAxIDAgUgo+PgpzdGFydHhyZWYKMzgwCiUlRU9GCg=="
        }
    ]
}

print(f"📡 Sending request to {url}...")
print(f"📦 Payload size: {len(str(payload))} chars")

try:
    start_time = time.time()
    response = requests.post(url, json=payload, timeout=120)
    duration = time.time() - start_time
    
    print(f"⏱️ Response time: {duration:.2f}s")
    print(f"🔢 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ SUCCESS: Task Created!")
        print(f"   Task ID: {data.get('task_id')}")
        print(f"   Project: {data.get('project_name')}")
        print(f"   Task Name: {data.get('task_name')}")
    else:
        print("\n❌ FAILED")
        print(response.text)

except Exception as e:
    print(f"❌ Connection Error: {e}")
