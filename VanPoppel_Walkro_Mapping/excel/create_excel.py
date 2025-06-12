from io import BytesIO
import logging
import openpyxl

def write_to_excel(json_string):
    # Create a new workbook and select the active sheet
    wb = openpyxl.Workbook()
    ws = wb.active

    data = json_string

    header1 = [
        "VAT exporter",
        "Contact",
        "Commericial reference",
        "Other ref",
        "Freight",
        "Goods location",
        "Export office",
        "Exit office",
        "Name",
        "Street + number",
        "Postcode",
        "city",
        "Country",
        "Inco Term",
        "Place",
        "Container",
        "Truck",
        "Rex/Other",
        "Vissel",
    ]
    
    values1 = [
        data.get('VAT exporter', ''),
        data.get('Principal', ''),
        data.get('Commericial reference', ''),
        data.get('Other Ref', ''),
        data.get('Freight', ''),
        data.get('kaai', ''),
        data.get('Export office', ''),
        data.get('Exit office', ''),
        data.get("Name",''),
        data.get("Street + number",''),
        data.get("Postcode",''),
        data.get("city",''),
        data.get("Country",''),
        data.get('Exit office', ''),
        data.get('Exit office', ''),
        data.get('Container'),
        data.get('Truck Nbr', ''),
        data.get("Customs Code", ''),
        data.get("Seal", ''),
    ]

    header2 = [
        "Commodity",
        "Description",
        "Article",
        "Collis",
        "Gross",
        "Net",
        "Origin",
        "Invoice value",
        "Currency",
        "Statistical Value",
        "Pieces",
        "Invoicenumber",
        "Invoice date",
        "Rex/other"
    ]
    
    rows_data = []  # To store the processed rows for "items"
    row_empty = []   # To store empty values for non-"items" keys
    
    for key, value in data.items():
        # Handle array values
        if key == "Items":
            for obj in value:
                mini_row = []
                for ordered_key in header2:
                    mini_row.append(obj.get(ordered_key, ''))
                rows_data.append(mini_row)
        else:
            row_empty.append("")

    # Add keys (headers) to the first row
    ws.append(header1)

    # Add values to the second row
    ws.append(values1)

    # Add empty rows and totals
    ws.append(row_empty)
    ws.append(row_empty)

    ws.append(["Total invoices"])
    ws.append([data.get("Total Value", 0)])
    ws.append(row_empty)

    ws.append(["Total Collis"])
    total_pallets = data.get('Total Pallets', 0)
    ws.append([total_pallets])
    ws.append(row_empty)

    ws.append(["Total Gross", "Total Net"])
    total_weight = data.get('Total Gross', 0)
    total_net = data.get('Total Net', 0)
    ws.append([total_weight, total_net])
    ws.append(row_empty)

    # Add items
    ws.append(["Items"])
    ws.append(header2)

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

