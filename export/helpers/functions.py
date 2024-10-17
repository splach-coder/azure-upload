import fitz  # PyMuPDF
import openpyxl
import json
from io import BytesIO
import re

def extract_key_value_pairs(text):
    lines = text.strip().splitlines()  # Split the text into individual lines
    key_value_pairs = {}  # Dictionary to store the key-value pairs
    current_key = None
    current_value = []
    extracting = False  # Flag to determine if we are within the extraction range

    for line in lines:
        line = line.strip()
        
        # Start extraction when we hit "Aangifte"
        if line == "Aangifte":
            extracting = True
        
        # Stop extraction after reaching "AEO nummer"
        if line == "AEO nummer":
            current_key = "AEO nummer"
            current_value = []  # Reset value for "AEO nummer"
            continue  # Skip the value assignment for now
        
        # If extraction hasn't started yet, continue
        if not extracting:
            continue

        # Check for separator lines
        if line == "_________________________________________________________________________":
            # If we have a current key, save the key and value
            if current_key:
                key_value_pairs[current_key] = " ".join(current_value).strip() if current_value else ""
            current_key = None
            current_value = []
        elif current_key is None:
            # Treat the first line after a separator as the key
            current_key = line
        else:
            # All subsequent lines are considered part of the value
            current_value.append(line)

    # Handle the last key-value pair
    if current_key:
        key_value_pairs[current_key] = " ".join(current_value).strip() if current_value else ""

    return key_value_pairs

def extract_text_from_pdf(pdf_path):
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    
    # Extract text from all pages
    text = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text += page.get_text()

    return text

def write_to_excel(json_string, number):
    # Create a new workbook and select the active sheet
    wb = openpyxl.Workbook()
    ws = wb.active

    data = json.loads(json_string)

    # Prepare row keys (headers) and row values
    row_keys = []
    row_values = []
    row_supp = []
    row_empty = []
    row_number = [number]


    for key, value in data.items():
        if key == "Exportformaliteiten te verrichten op een":
            break

        row_keys.append(key)

        # Handle array values
        if isinstance(value, list):
            if len(value) > 0:
                row_values.append(value[0])
                if len(value) > 1:
                    row_supp.append(value[1])  # Add second element of array to supplemental row
                else:
                    row_supp.append("")  # Add empty string if no second element
            else:
                row_values.append("")
                row_supp.append("")
        else:
            row_values.append(value)
            row_supp.append("")

    # Add keys (headers) to the first row
    ws.append(row_keys)

    # Add values to the second row
    ws.append(row_values)

    # Add supplemental row if there are values for it
    if any(row_supp):
        ws.append(row_supp)

    # Add values to the second row
    ws.append(row_empty)  
    ws.append(row_number)  

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

def correct_number_format(value):
    # Remove periods and replace commas with periods
    corrected_value = re.sub(r'\.', '', value)  # Remove periods
    corrected_value = re.sub(r'(?<=\d),(?=\d)', '.', corrected_value)  # Replace comma with period if it’s between numbers
    return float(corrected_value)

def modify_and_correct_amounts(data):
    # Ensure the input is a string and convert to dictionary
    if isinstance(data, str):
        data = json.loads(data)  # Convert JSON string to dictionary
    elif not isinstance(data, dict):
        raise TypeError("Input must be a JSON string or a dictionary.")
    
    # Modify the specified keys by splitting their values
    for key in ["Aanvullende eenheden", "Nettogewicht", "Brutogewicht"]:
        if key in data:
            value = data[key]
            # Split the value into amount and currency
            corrected_amount = correct_number_format(value)  # Correct the number format
            data[key] = corrected_amount  # Update the value to be an array

    # Modify the specified keys by splitting their values
    for key in ["Totaal gefactureerd bedrag", "Statistische waarde"]:
        if key in data:
            value = data[key]
            # Split the value into amount and currency
            amount, currency = value.split()  # Assuming the format is "amount currency"
            corrected_amount = correct_number_format(amount)  # Correct the number format
            data[key] = [corrected_amount, currency]  # Update the value to be an array

    return json.dumps(data, indent=2)

def extract_kantoor_number(email_body: str) -> str:
    """
    This function searches for the number immediately following 'Kantoor;' 
    in the email body and returns it. It stops at the first non-digit character.
    
    :param email_body: The text containing the email body
    :return: The extracted number as a string or 'None' if not found
    """
    # Regex pattern to match "Kantoor;" followed by a number, stopping at the first space or non-digit character
    pattern = r"Kantoor;\s*(\d+)\b"
    
    # Search for the pattern in the email body
    match = re.search(pattern, email_body)
    
    # Return the number if found, otherwise return None
    if match:
        return match.group(1)
    return None

