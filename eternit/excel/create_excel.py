from datetime import datetime
from io import BytesIO
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
        "ILS number"
    ]

    address = data.get('Adress', [])
    name, street, city, code_postal, country = address#.get('Company', ''), address.get('Street', ''), address.get('City', ''), address.get('Postal code', ''), address.get('Country', '') 

    term, place = data.get('Incoterm', ['', ''])
    
    Total = data.get('Total', 0.00)
    Freight = data.get('Freight', 0.00)
    
    vat_number = data.get('Vat number', '')
    if not vat_number:
        vat_number = data.get('Eori number', '')
    
    values1 = [
        data.get('Vat number', ''),
        data.get('Principal', ''),
        data.get('Inv Reference', ''),
        data.get('Bon de livraison', ''),
        Freight,
        data.get('Parking trailer', ''),
        data.get('Export office', ''),
        data.get('Exit office', ''),
        name if 'name' in locals() else '',  # Safely handle variables
        street if 'street' in locals() else '',
        code_postal if 'code_postal' in locals() else '',
        city if 'city' in locals() else '',
        country if 'country' in locals() else '',
        term if 'term' in locals() else '',
        place if 'place' in locals() else '',
        data.get('container', ''),
        data.get('Wagon', ''),
        data.get("Customs Code", ''),
        data.get("ILS_NUMBER", '')
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
        if key == "Summary":
            for obj in value:
                mini_row = []
                for ordered_key in header2:
                    # Append the value in the desired order, or an empty string if the key is missing
                    if ordered_key == "Commodity":
                        mini_row.append(obj.get("HS", ''))
                    elif ordered_key == "Gross":
                        mini_row.append(obj.get("Gross Weight", ""))
                    elif ordered_key == "Net":
                        mini_row.append(obj.get("Net Weight", ""))
                    elif ordered_key == "Invoice value":
                        mini_row.append(obj.get("Value", ""))
                    elif ordered_key == "Pieces":
                        mini_row.append(obj.get("Qty", ""))
                    elif ordered_key == "Currency":
                        mini_row.append(data.get("Currency", ''))
                    elif ordered_key == "Invoicenumber":
                        mini_row.append(obj.get("Inv Reference", ''))
                    elif ordered_key == "Invoice date":
                        # Convert string to date if possible
                        inv_date_str = data.get("Inv Date", '')
                        try:
                            inv_date = datetime.strptime(inv_date_str, "%d.%m.%Y").date()  # Adjust format as needed
                            mini_row.append(inv_date)
                        except ValueError:
                            mini_row.append(inv_date_str)  # If conversion fails, keep as string
                    elif ordered_key == "Rex/other":
                        mini_row.append(data.get("Customs Code", ''))
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
    ws.append([Total])
    ws.append(row_empty)

    ws.append(["Total Collis"])
    total_pallets = data.get('Total pallets', 0)
    ws.append([total_pallets])
    ws.append(row_empty)

    ws.append(["Total Gross", "Total Net"])
    total_weight = data.get('Gross weight Total', 0)
    total_Netweight = data.get('Net weight Total', 0)
    ws.append([total_weight, total_Netweight])
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
