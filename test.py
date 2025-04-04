result = {
    "vat_importer": "BE0401574852",
    "eori_importer": "BE0401.574.852",
    "commercial_reference": "51032966",
    "incoterm": "DPU",
    "place": "ANTWERP",
    "entrepot": "U-00160-A",
    "License": "ET 90.500/12",
    "Vak 24": "11",
    "Vak 37": "4500",
    "Vak 44": "BEVALA00011",
    "Items": [
        {
            "other_reference": "137241000",
            "commodity": "7112990000",
            "description": "SWEEPS FROM MIXED ELECTRONIC COMPONENTS",
            "origin": "JP",
            "invoice_value": 1330023.1,
            "currency": "USD",
            "cost center": "HBN5092",
            "kaai": "KAAI 1700",
            "agent": "MSCBEL",
            "lloydsnummer": "9839272",
            "verblijfsnummer": "293278",
            "bl": "MEDUPQ337602",
            "artikel_nummer": "0040",
            "item": "001",
            "kp": "HBN5101",
            "contract_number": "137241000",
            "company": "YOKOHAMA METAL CO LTD",
            "container": "TGBU6861254",
            "packages": 11,
            "gross_weight": 7.453,
            "net_weight": 6.292
        },
        {
            "other_reference": "137242000",
            "commodity": "7112990000",
            "description": "HIGH MOISTURE BUFFING RESIDUE",
            "origin": "JP",
            "invoice_value": 61181.49,
            "currency": "USD",
            "cost center": "HBN5092",
            "kaai": "KAAI 1700",
            "agent": "MSCBEL",
            "lloydsnummer": "9839272",
            "verblijfsnummer": "293278",
            "bl": "MEDUPQ337602",
            "artikel_nummer": "0040",
            "item": "001",
            "kp": "HBN5092",
            "contract_number": "137242000",
            "company": "YOKOHAMA METAL CO LTD",
            "container": "TGBU6861254",
            "packages": 9,
            "gross_weight": 12.235,
            "net_weight": 12.044
        }
    ]
}

# Calculate totals from the Items list directly
result["Total packages"] = sum(item.get("packages", 0) for item in result.get("Items", []))
result["Total gross"] = sum(item.get("gross_weight", 0) for item in result.get("Items", []))
result["Total net"] = sum(item.get("net_weight", 0) for item in result.get("Items", []))
result["Total Value"] = sum(item.get("invoice_value", 0) for item in result.get("Items", []))

print(result)