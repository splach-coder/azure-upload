from io import BytesIO
import openpyxl

def write_to_excel(json_string):
    # Create a new workbook and select the active sheet
    wb = openpyxl.Workbook()
    ws = wb.active

    data = json_string

    header1 = [
        "VAT exporter",
        "EORI importer",
        "Contact",
        "Commericial reference",
        "Other ref",
        "Freight",
        "VAT cost",
        "Goods location",
        "Validation office",
        "Suppliername",
        "Street + number",
        "Postcode",
        "city",
        "Country",
        "Inco Term",
        "Place",
        "Truck",
        "Entrepot",
        "License",
        "Vak 24",
        "Vak 37",
        "Vak 44",
        "Kostenplaats"
    ]

    values1 = [
        data.get('vat_importer', ''),
        data.get('eori_importer', '').replace('.', ''),
        '',
        data.get('commercial_reference', ''),
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        data.get('incoterm', ''),
        data.get('place', ''),
        '',
        data.get('entrepot', ''),
        data.get('License', ''),
        data.get('Vak 24', ''),
        data.get('Vak 37', ''),
        data.get('Vak 44', '')
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
        "Pieces",
        "Invoicenumber",
        "Invoice date",
        "Container",
        "Loyds",
        "Verblijfs",
        "Agent",
        "article",
        "Item",
        "BL",
        "Kostenplaats"
    ]
    
    rows_data = []  # To store the processed rows for "items"
    row_empty = []   # To store empty values for non-"items" keys
    
    for key, value in data.items():
        # Handle array values
        if key == "Items":
            for obj in value:
                mini_row = []
                for ordered_key in header2:
                    # Append the value in the desired order, or an empty string if the key is missing
                    if ordered_key == "Commodity":
                        mini_row.append(obj.get("commodity", ''))
                    elif ordered_key == "Description":
                        mini_row.append(obj.get("description", ''))
                    elif ordered_key == "Collis":
                        mini_row.append(obj.get("packages", ''))
                    elif ordered_key == "Gross":
                        mini_row.append(obj.get("gross_weight", ''))
                    elif ordered_key == "Net":
                        mini_row.append(obj.get("net_weight", ''))
                    elif ordered_key == "Origin":
                        mini_row.append(obj.get("origin", ''))
                    elif ordered_key == "Invoice value":
                        mini_row.append(obj.get("invoice_value", ''))
                    elif ordered_key == "Container":
                        mini_row.append(obj.get("container", ''))
                    elif ordered_key == "Loyds":
                        mini_row.append(f'L{obj.get("lloydsnummer", "")}')
                    elif ordered_key == "Verblijfs":
                        mini_row.append(obj.get("verblijfsnummer", ''))
                    elif ordered_key == "Agent":
                        mini_row.append(obj.get("agent", ''))
                    elif ordered_key == "article":
                        mini_row.append(obj.get("artikel_nummer", ''))
                    elif ordered_key == "Item":
                        mini_row.append(obj.get("item", ''))
                    elif ordered_key == "BL":
                        mini_row.append(obj.get("bl", ''))
                    elif ordered_key == "Kostenplaats":
                        mini_row.append(obj.get("kp", ''))
                    else:    
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
    ws.append([data.get('Total Value', 0)])
    ws.append(row_empty)

    ws.append(["Total Collis"])
    total_pallets = data.get('Total packages', 0)
    ws.append([total_pallets])
    ws.append(row_empty)

    ws.append(["Total Gross", "Total Net"])
    total_weight = data.get('Total gross', 0)
    total_net = data.get('Total net', 0)
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

