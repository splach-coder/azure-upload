import json


extra_file_excel_data = {
    "rows": [
        {
            "Customs code": "BEIPOH00035",
            "Bill. Doc.": "97213739",
            "Comm. Code": "32141010",
            "Gross": 15702.336,
            "Net weight": 11978.928,
            "Net Value": 31168.8,
            "Currency": "GBP",
            "# Collies": 0
        },
        {
            "Customs code": "BEIPOH00035",
            "Bill. Doc.": "97213739",
            "Comm. Code": "",
            "Gross": 15702.336,
            "Net weight": 11978.928,
            "Net Value": 31168.8,
            "Currency": "GBP",
            "# Collies": 0
        },
        {
            "Customs code": "BEIPOH00035",
            "Bill. Doc.": "",
            "Comm. Code": "",
            "Gross": 15702.336,
            "Net weight": 11978.928,
            "Net Value": 31168.8,
            "Currency": "GBP",
            "SubTotal": True,
            "# Collies": 26
        },
        {
            "Customs code": "",
            "Bill. Doc.": "",
            "Comm. Code": "",
            "Gross": 15702.336,
            "Net weight": 11978.928,
            "Net Value": 31168.8,
            "Currency": "GBP",
            "GrandTotal": True
        }
    ]
}

extra_file_excel_data["rows"] = [
    row for row in extra_file_excel_data.get("rows", [])
    if not (('GrandTotal' in row and row['GrandTotal'] == True) or ('SubTotal' in row and row['SubTotal'] == True))
]

print(json.dumps(extra_file_excel_data, indent=4, ensure_ascii=False))