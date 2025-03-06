from collections import defaultdict
import difflib

invoices = [
    {
        "Inv Date": "27.02.2025",
        "Other Ref": "92063439",
        "Vat Number": "BE0452407307",
        "Gross weight Total": 430.2,
        "Total": 145497.52,
        "Currency": "EUR",
        "Items": [
            {
                "HS Code": "3005909900",
                "COO": "US",
                "Net": 5.59,
                "Gross": 7.36,
                "Amount": 829.44,
                "Qty": 0,
                "Inv Ref": "92063439"
            },
            {
                "HS Code": "3006400000",
                "COO": "JP",
                "Net": 190.97,
                "Gross": 276.32,
                "Amount": 138574.25,
                "Qty": 0,
                "Inv Ref": "92063439"
            },
            {
                "HS Code": "3006400000",
                "COO": "US",
                "Net": 10.68,
                "Gross": 13.85,
                "Amount": 1769.4,
                "Qty": 0,
                "Inv Ref": "92063439"
            },
            {
                "HS Code": "3306100000",
                "COO": "JP",
                "Net": 0.08,
                "Gross": 0.09,
                "Amount": 111.95,
                "Qty": 0,
                "Inv Ref": "92063439"
            },
            {
                "HS Code": "3306100000",
                "COO": "US",
                "Net": 1.2,
                "Gross": 2.09,
                "Amount": 336.42,
                "Qty": 0,
                "Inv Ref": "92063439"
            },
            {
                "HS Code": "3306900000",
                "COO": "JP",
                "Net": 0.75,
                "Gross": 0.8,
                "Amount": 220.32,
                "Qty": 0,
                "Inv Ref": "92063439"
            },
            {
                "HS Code": "3407000000",
                "COO": "JP",
                "Net": 1.5,
                "Gross": 1.7,
                "Amount": 361.0,
                "Qty": 0,
                "Inv Ref": "92063439"
            },
            {
                "HS Code": "3506100000",
                "COO": "JP",
                "Net": 1.2,
                "Gross": 1.65,
                "Amount": 1708.8,
                "Qty": 0,
                "Inv Ref": "92063439"
            },
            {
                "HS Code": "3906100000",
                "COO": "US",
                "Net": 4.8,
                "Gross": 6.06,
                "Amount": 1217.76,
                "Qty": 0,
                "Inv Ref": "92063439"
            },
            {
                "HS Code": "3906901000",
                "COO": "JP",
                "Gross": 0.35,
                "Amount": 200.8,
                "Net": 0.0,
                "Qty": 0,
                "Inv Ref": "92063439"
            },
            {
                "HS Code": "6805300000",
                "COO": "JP",
                "Net": 0.5,
                "Gross": 0.52,
                "Amount": 167.38,
                "Qty": 0,
                "Inv Ref": "92063439"
            }
        ],
        "Address": [
            "Muratbey Gumruk Mudurlugu",
            "Guzide Sokak No:20",
            "\u0130stanbul",
            "34303",
            "TR"
        ],
        "Inv Reference": "92063439",
        "Incoterm": [
            "",
            ""
        ],
        "Customs Code": ""
    },
    {
        "Inv Reference": "9400012859",
        "Inv Date": "26.02.2025",
        "Other Ref": "92057690",
        "Vat Number": "BE0452407307",
        "Incoterm": [
            "CIP",
            "\u00c7atalca - Istanbul"
        ],
        "Gross weight Total": 153.82,
        "Total": 30000.0,
        "Currency": "EUR",
        "Items": [
            {
                "HS Code": "3006400000",
                "COO": "JP",
                "Net": 51.0,
                "Gross": 88.95,
                "Amount": 30000.0,
                "Qty": 0,
                "Inv Ref": "9400012859"
            }
        ],
        "Address": [],
        "Customs Code": ""
    }
]

def normalize_address(address):
    """Normalize full address for comparison."""
    address_fields = [
        address[0] ,
        address[1] ,
        address[2] ,
        address[3] ,
        address[4] 
    ]
    return ' '.join(str(field).lower() for field in address_fields if field)
    
def are_addresses_similar(addr1, addr2, threshold):
    """Determine if two addresses are similar based on a similarity ratio."""
    if len(addr1) > 0 or len(addr2) > 0:
        return True 
    ratio = difflib.SequenceMatcher(None, addr1, addr2).ratio()
    return ratio >= threshold

# Group invoices by similar addresses
grouped_invoices = defaultdict(list)
processed_addresses = []

for invoice in invoices:
    if len(invoice.get('Address', [])) > 0:  
        address = normalize_address(invoice.get('Address', []))
    else :
        address = []    
    matched_group = None

    # Find a matching group for the current address
    for group_addr in processed_addresses:
        if are_addresses_similar(address, group_addr, 0.8):
            matched_group = group_addr
            break

    # Handle empty address scenario
    if not matched_group and not address:
        # Merge with the first group if exists, else create new
        if processed_addresses:
            matched_group = processed_addresses[0]
        else:
            matched_group = address

    # Add to the matched group or create a new group
    if matched_group:
        grouped_invoices[matched_group].append(invoice)
    else:
        grouped_invoices[address].append(invoice)
        processed_addresses.append(address)

# Combine grouped invoices
combined_invoices = []
for group, group_invoices in grouped_invoices.items():
    if len(group_invoices) == 1:
        # No combination needed
        combined_invoices.append(group_invoices[0])
    else:
        # Combine invoices
        combined_invoice = {
            "Inv Ref": " + ".join(inv["Inv Reference"] for inv in group_invoices),
            "Inv Date": group_invoices[0]["Inv Date"],
            "Other Ref": group_invoices[0]["Other Ref"],
            "Incoterm": group_invoices[0]["Incoterm"],
            "Currency": group_invoices[0]["Currency"],
            "Customs Code": group_invoices[0]["Customs Code"],
            "Adrress": group_invoices[0]["Address"],
            "Items": [item for inv in group_invoices for item in inv.get("Items", [])],
            "Totals": {
                "Total Qty": sum(item.get("Qty", 0) for inv in group_invoices for item in inv.get("Items", [])),
                "Total Gross": sum(item.get("Gross", 0) for inv in group_invoices for item in inv.get("Items", [])),
                "Total Net": sum(item.get("Net", 0) for inv in group_invoices for item in inv.get("Items", [])),
                "Total Amount": sum(item.get("Amount", 0) for inv in group_invoices for item in inv.get("Items", [])),
            }
        }
        combined_invoices.append(combined_invoice)
      
print(combined_invoices)