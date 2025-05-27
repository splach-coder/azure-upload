from io import BytesIO
import logging
import openpyxl

def write_to_excel(json_string):
    # Create a new workbook and select the active sheet
    wb = openpyxl.Workbook()
    ws = wb.active

    data = json_string

    header = [
        "FIDNO",
        "",
        "FREIGHT COST",
        "",
        "Freight cost valuta",
        "",
        "USD"
    ] 
    
    header_values = [
        f"FID{data.get('Contract No', '')}",
        "",
        data.get('Freight', ''), 
        "",
        data.get('InsuranceCurrency', ''),
        "",
        data.get('ExchangeCalc', ''),
    ]

    items_header = [
        "INVOICENUMBER",
        "INVOICEDATE",
        "DESCRIPTION OF GOODS",
        "HS CODE",
        "CARTON",
        "QUANTITY-SET",
        "UNIT PRICE",
        "TOTAL VALUE",
        "VALUTA",
        "GROSS",
        "NET",
        "INSURANCE",
        "VATNO",
        "EORI",
    ]
    
    rows_data = []  # To store the processed rows for "items"
    row_empty = []   # To store empty values for non-"items" keys
    
    for key, value in data.items():
        logging.error(f"Processing key: {key}")
        # Handle array values
        if key == "items":
            for obj in value:
                mini_row = []
                
                for ordered_key in items_header:
                    # Append the value in the desired order, or an empty string if the key is missing
                    if ordered_key == "INVOICENUMBER":
                        mini_row.append(obj.get("Contract No", ''))
                    elif ordered_key == "INVOICEDATE":
                        mini_row.append(obj.get("Contract Date", ''))
                    elif ordered_key == "DESCRIPTION OF GOODS":
                        mini_row.append(obj.get("Description", ''))
                    elif ordered_key == "HS CODE":
                        mini_row.append(obj.get("HS Code", ''))
                    elif ordered_key == "QUANTITY-SET":
                        mini_row.append(obj.get("SET", ''))
                    elif ordered_key == "UNIT PRICE":
                        mini_row.append(obj.get("Unit Price", ""))
                    elif ordered_key == "TOTAL VALUE":
                        mini_row.append(obj.get("Amount", ''))
                    elif ordered_key == "GROSS":
                        mini_row.append(obj.get("Gross Weight", ''))
                    elif ordered_key == "NET":
                        mini_row.append(obj.get("Net Weight", ''))
                    elif ordered_key == "INSURANCE":
                        mini_row.append(obj.get("InsuranceAmount", ''))
                    elif ordered_key == "VATNO":
                        mini_row.append(obj.get("VAT No", ''))
                    elif ordered_key == "EORI":
                        mini_row.append(obj.get("EORI No", ''))
                    else:    
                        mini_row.append(obj.get(ordered_key, ''))
                rows_data.append(mini_row)
        else:
            row_empty.append("")

    # Add keys (headers) to the first row
    ws.append(header)

    # Add values to the second row
    ws.append(header_values)

    # Add empty rows and totals
    ws.append(row_empty)

    # Add items
    ws.append(items_header)

    for arr in rows_data:
        ws.append(arr)

    # Optionally, adjust column widths for better formatting
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter  # Get the column name
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width

    # Save the workbook to a BytesIO object (in memory)
    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    return file_stream

