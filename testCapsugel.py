import difflib
from collections import defaultdict


invoices = [
    {
        "Inv Ref": "999606850",
        "Inv Date": "10.12.2024",
        "Other Ref": "8671",
        "Incoterm": [
            "DDP",
            "RISHON LETSIYON"
        ],
        "Currency": "USD",
        "Customs Code": "BE1489",
        "Adrress": [
            {
                "Company name": "AGORAN\nAvraham",
                "Street": "Buma Shavit 3 St.\nLEV SOREQ",
                "City": "booth 16\nRISHON LETSIYON",
                "Country": "ISRA\u00cbL",
                "Postal code": None
            }
        ],
        "Items": [
            {
                "Origin": "BE",
                "HS code": "4910000000",
                "Qty": 15,
                "Gross": 4.81,
                "Net": 4.5,
                "Amount": 34.6
            }
        ],
        "Totals": [
            {
                "Total Qty": 15,
                "Total Gross": 4.81,
                "Total Net": 4.5,
                "Total Amount": 34.6
            }
        ]
    },
    {
        "Inv Ref": "999606849",
        "Inv Date": "10.12.2024",
        "Other Ref": "8671",
        "Incoterm": [
            "DAP",
            "RISHON LETSIYON"
        ],
        "Currency": "USD",
        "Customs Code": "BE1489",
        "Adrress": [
            {
                "Company name": "AGORAN",
                "Street": "Avraham Buma Shavit 3 St.\nLEV SOREQ",
                "City": "booth 16\nRISHON LETSIYON",
                "Country": "ISRA\u00cbL",
                "Postal code": None
            }
        ],
        "Items": [
            {
                "Origin": "US",
                "HS code": "7326909890",
                "Qty": 9,
                "Gross": 10.73,
                "Net": 10.04,
                "Amount": 1142.79
            }
        ],
        "Totals": [
            {
                "Total Qty": 9,
                "Total Gross": 10.73,
                "Total Net": 10.04,
                "Total Amount": 1142.79
            }
        ]
    }
]

def normalize_address(address):
  """Normalize full address for comparison."""
  address_fields = [
      address[0]['Company name'],
      address[0]['Street'],
      address[0]['City'],
      address[0]['Postal code'],
      address[0]['Country']
  ]
  return ' '.join(str(field).lower() for field in address_fields if field)
      
def are_addresses_similar(addr1, addr2, threshold):
  """Determine if two addresses are similar based on a similarity ratio."""
  ratio = difflib.SequenceMatcher(None, addr1, addr2).ratio()
  print(ratio)
  return ratio >= threshold

addr1 = invoices[0].get('Adrress')
addr2 = invoices[1].get('Adrress')


addr1 = normalize_address(addr1)
addr2 = normalize_address(addr2)
threshold = 0.8

def fill_origin_country_on_items(items: list) -> list:
    origin = ""
    for item in items:
        if item.get("Origin") is not None:
            origin = item.get("Origin")
        else :
            item["Origin"] = origin
            
    return items        
        
print(fill_origin_country_on_items(invoices[1].get('Items')))        