from eternit.functions.functions import normalize_numbers, safe_int_conversion


Items = [
        {
            "Qty": "432",
            "Origin": "Belgium",
            "Pcs": "1,000",
            "Value": "4,637.77",
            "Freight": "430.23",
            "VAT": "B6",
            "C.T": "01"
        },
        {
            "Qty": "88",
            "Origin": "Denmark",
            "Pcs": "1,000",
            "Value": "842.13",
            "Freight": "6.19",
            "VAT": "B6",
            "C.T": "02"
        },
        {
            "Qty": "30",
            "Origin": "Denmark",
            "Pcs": "1,000",
            "Value": "163.51",
            "Freight": "1.46",
            "VAT": "B6",
            "C.T": "02"
        },
        {
            "Qty": "15",
            "Origin": "Germany",
            "Pcs": "1,000",
            "Value": "672.89",
            "Freight": "4.09",
            "VAT": "B6",
            "C.T": "03"
        },
        {
            "Qty": "66",
            "Origin": "Denmark",
            "Pcs": "1,000",
            "Value": "390.33",
            "Freight": "2.22",
            "VAT": "B6",
            "C.T": "02"
        },
        {
            "Qty": "6",
            "Origin": "France",
            "Pcs": "1,000",
            "Value": "32.62",
            "Freight": "0.31",
            "VAT": "B6",
            "C.T": "04"
        }
    ]

            #update the numbers in the items

for item in Items :
    #handle the Qty
    Qty = item.get("Qty", "")
    Qty = normalize_numbers(Qty)
    Qty = safe_int_conversion(Qty)
    item["Qty"] = Qty
    
    #handle the Pcs
    Pcs = item.get("Pcs", "")
    Pcs = normalize_numbers(Pcs)
    print(f"Pcs: {Pcs}") 
    Pcs = safe_int_conversion(Pcs)   
    item["Pcs"] = Pcs
    
