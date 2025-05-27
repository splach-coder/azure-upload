from io import BytesIO
import logging
import openpyxl

def write_to_excel(json_string):
    logging.info("Starting to write to Excel")
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
        f"{data.get('INVOICENUMBER', '')}",
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

