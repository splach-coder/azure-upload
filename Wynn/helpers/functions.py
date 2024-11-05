from io import BytesIO
import json
from openpyxl.styles import Font, PatternFill
import re

import openpyxl

def extract_currency_symbol(cell):
    """
    Extract the currency symbol from an Excel cell's number format.
    """
    # Define known currency symbols
    currency_symbols = {
        '€': 'Euro',
        '$': 'Dollar',
        '£': 'Pound',
        '¥': 'Yen',
        '₹': 'Rupee',
        '₩': 'Won',
        '₽': 'Ruble',
        '₺': 'Lira',
        '₨': 'Rupee',
        '₦': 'Naira',
        '฿': 'Baht',
        '₫': 'Dong'
    }

    # Extract the number format from the cell
    currency_format = cell.number_format

    # Find the currency symbol
    for symbol in currency_symbols:
        if symbol in currency_format:
            return symbol

    return 'Unknown'  # Default if no known currency symbol is found

def clean_string(input_string):
    # Use regex to match only alphanumeric characters
    cleaned_string = re.sub(r'[^a-zA-Z0-9]', '', input_string)
    return cleaned_string    

def extract_valid_container(container_string):
    if container_string:
        container = clean_string(container_string)

        # Check if the container matches the format 4 chars and 7 digits
        pattern = r'^[A-Z]{4}\d{7}$'
        if not re.match(pattern, container):
            return False

        return container
    else :
        return False
    
def write_to_excel(json_string):
    # Create a new workbook and select the active sheet
    wb = openpyxl.Workbook()
    ws = wb.active

    data = json_string

    row_keys = []
    row_values = []
    row_empty = []

    rows_data = []

    header = [
        "Invoicenumber",
        "Client",
        "Commodity",
        "Partnumber",
        "Description",
        "Packaging",
        "Origin",
        "Invoiced",
        "Unit",
        "Pieces",
        "Gross",
        "Net",
        "EXW value",
        "Cif Value",
        "Fob Value"
    ]

    for key, value in data.items():
        # Handle array values
        if key == "items":
            #logic here
            for obj in value:
                mini_row = []
                for key2, value2 in obj.items():
                    mini_row.append(value2)
                rows_data.append(mini_row)
        else:
            row_keys.append(key)
            row_values.append(value)
            row_empty.append("")

    # Add keys (headers) to the first row
    ws.append(row_keys)

    # Add values to the second row
    ws.append(row_values)

        # Add values to the second row
    ws.append(row_empty)

    # Add values to the second row
    ws.append(header)

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

    # Iterate through rows with enumerate to get the row index
    for i, row in enumerate(ws.iter_rows(), start=1):  # Use ws.iter_rows() and start from 1
        # Make the first row bold
        if i == 1:
            for cell in row:
                cell.font = Font(bold=True)
        
        # Fill the fourth row with a yellow background color
        if i == 4:
            for cell in row:
                if cell.value :
                    cell.font = Font(bold=True)
                    cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
    
    # Save the workbook to a BytesIO object (in memory)
    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    return file_stream

def format_float_values(data):
    for item in data:
        for key, value in item.items():
            if isinstance(value, float):
                item[key] = round(value, 2)  # Round to two decimal places
    return data