import requests
import sys

def search(query):
    # Using the Donna conductor's endpoint to check if it can find it
    # Or calling Memory service directly
    url = "http://localhost:7071/api/DonnaMemory"
    payload = {
        "action": "find_duplicate",
        "text": query,
        "resource_type": "odoo_project", # Updated to match my enrich_from_odoo type
        "threshold": 0.5
    }
    print(f"🔍 Searching memory for: '{query}'")
    resp = requests.post(url, json=payload)
    if resp.status_code == 200:
        data = resp.json()
        if data.get("duplicate"):
            dup = data["duplicate"]
            print(f"✅ FOUND: {dup['metadata'].get('chunk_text')[:50]}... (ID: {dup['id']})")
            print(f"   Score: {dup['score']}")
        else:
            print("❌ No match found in memory.")
    else:
        print(f"Error: {resp.status_code}")
        print(resp.text)

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "Arrival NCTS"
    search(q)
