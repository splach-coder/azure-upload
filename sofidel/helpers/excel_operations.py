from io import BytesIO
import json
from openpyxl.styles import Font, PatternFill
import re
import openpyxl

from sofidel.utils.number_handlers import clean_string, normalize_number_format, safe_int_conversion, safe_float_conversion


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
        "Rex/Other"
    ]

    name, street, city, code_postal, country = data['address']

    # Split the string into parts
    parts = data['term'].split(maxsplit=1)

    # Extract the first word and the rest
    term = parts[0] if parts else ''  # The first word
    place = parts[1] if len(parts) > 1 else ''  # Everything after the first word

    values1 = [
        clean_string(data.get('btw', '')),
        data.get('Principal', ''),
        data.get('Reference', ''),
        data.get('inv reference', ''),
        data.get('Freight cost', ''),
        data.get('Parking trailer', ''),
        data.get('Export office', ''),
        data.get('Exit Port BE', ''),
        name if 'name' in locals() else '',  # Safely handle variables
        street if 'street' in locals() else '',
        code_postal if 'code_postal' in locals() else '',
        city if 'city' in locals() else '',
        country if 'country' in locals() else '',
        term if 'term' in locals() else '',
        place if 'place' in locals() else '',
        data.get('Container', ''),
        data.get('wagon', ''),
        data.get('rex', ''),
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
        if key == "items":
            for obj in value:
                mini_row = []
                for ordered_key in header2:
                    # Append the value in the desired order, or an empty string if the key is missing
                    if(ordered_key == "Currency"):
                        mini_row.append(data.get("currency", ''))
                    elif(ordered_key == "Invoicenumber"):
                        mini_row.append(data.get("inv reference", ''))
                    elif(ordered_key == "Invoice date"):
                        mini_row.append(data.get("inv date", ''))
                    elif(ordered_key == "Rex/other"):
                        mini_row.append(data.get("rex", ''))
                    else:    
                        mini_row.append(obj.get(ordered_key, ''))
                rows_data.append(mini_row)
        else:
            row_empty.append("")

    # Add keys (headers) to the first row
    ws.append(header1)
    # Add values to the second row
    ws.append(values1)

    # Add values to the second row
    ws.append(row_empty)
    ws.append(row_empty)

    # Add values 
    ws.append(["Total invoices"])
    total_invoices = safe_float_conversion(normalize_number_format(data.get('total amount', 0)))
    ws.append([total_invoices])
    ws.append(row_empty)

    # Add values 
    ws.append(["Total Collis"])
    total_pallets = safe_int_conversion(normalize_number_format(data.get('total pallets', 0)))
    ws.append([total_pallets])
    ws.append(row_empty)

    # Add values 
    ws.append(["Total Gross"])
    total_weight = safe_float_conversion(normalize_number_format(data.get('total weight', 0)))
    ws.append([total_weight])
    ws.append(row_empty)

    # Add values
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
