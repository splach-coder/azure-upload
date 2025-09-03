from datetime import datetime
import re
import fitz

def clean_incoterm(incoterm):
    if not incoterm:
        return ["", ""]
    
    #split the incoterm by comma
    incoterm_parts = incoterm.split(",")
    
    #each part should be stripped of leading and trailing spaces
    incoterm_parts = [part.strip() for part in incoterm_parts]
    
    return incoterm_parts

def clean_customs_code(value: str) -> str:
    if value is None:
        return ""
    return value.replace(')', '').replace(' ', '').replace(",", "")

def detect_pdf_type(pdf_path):
    try:
        # Open the PDF file
        pdf_document = fitz.open(pdf_path)
        
        # Ensure the PDF has at least 1 page
        if len(pdf_document) < 1:
            return "The PDF is empty or has no pages."

        # Get the first page
        first_page = pdf_document[0]

        # Extract the text from the first page
        first_page_text = first_page.get_text("text")

        # Check for the keywords 'Packing List' and 'Invoice'
        if "Packing List" in first_page_text:
            return "Packing List"
        elif "Invoice" in first_page_text:
            return "Invoice"
        else:
            return "I can't detect which PDF it is."

    except Exception as e:
        return f"An error occurred: {str(e)}"
    
def transform_date(date_str):
    # Parse the date string
    parsed_date = datetime.strptime(date_str, '%d-%b-%Y')
    # Format the date to desired output
    formatted_date = parsed_date.strftime('%d.%m.%Y')
    return formatted_date

def safe_int_conversion(value: str) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

def safe_float_conversion(value: str) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def safe_lower(var):
    """
    Returns the lower-case version of var if it is not None,
    otherwise returns an empty string.
    """
    if var is None:
        return ""
    return var.lower()

def normalize_number(value: str) -> str:
    return value.replace(" ", "").replace(",", "")

def merge_factuur_objects(factuur_array):
    """
    Merge multiple factuur objects into a single consolidated object.
    
    Args:
        factuur_array (list): Array of factuur objects to merge
        
    Returns:
        dict: Merged factuur object
    """
    if not factuur_array:
        return {}
    
    if len(factuur_array) == 1:
        return factuur_array[0]
    
    # Start with the first object as base
    merged = factuur_array[0].copy()
    
    # Fields that should be summed (numeric fields)
    numeric_fields = [
        "Total Gross", "Total Net", "Total Value", "Total Pallets"
    ]
    
    # Fields that should be concatenated if different (text fields)
    text_fields = [
        "Inv Number", "Other Ref", "Truck Nbr", "Container", "Seal", "Filename"
    ]
    
    # Fields that should remain the same (use first object's value)
    # These are typically consistent across related invoices
    consistent_fields = [
        "Address", "Cust Nbr", "Incoterm", "Inv Date", "Rex Number", 
        "VAT", "Customs Code", "Currency", "File Type", "Reference"
    ]
    
    # Initialize merged Items array
    merged["Items"] = []
    
    # Process each factuur object
    for factuur in factuur_array:
        # Add all items to the merged items array
        if "Items" in factuur and factuur["Items"]:
            merged["Items"].extend(factuur["Items"])
    
    # Process remaining objects (skip first one since it's our base)
    for i in range(1, len(factuur_array)):
        current_factuur = factuur_array[i]
        
        # Handle numeric fields - sum them up
        for field in numeric_fields:
            if field in current_factuur and field in merged:
                current_val = current_factuur[field] if current_factuur[field] is not None else 0
                merged_val = merged[field] if merged[field] is not None else 0
                merged[field] = merged_val + current_val
        
        # Handle text fields - concatenate if different
        for field in text_fields:
            if field in current_factuur and field in merged:
                current_val = current_factuur[field]
                merged_val = merged[field]
                
                # Skip if either is None or empty
                if not current_val or not merged_val:
                    continue
                    
                # If values are different, concatenate with ' + '
                if str(current_val).strip() != str(merged_val).strip():
                    if ' + ' not in str(merged_val):  # Avoid duplicate concatenation
                        merged[field] = str(merged_val) + ' + ' + str(current_val)
                    elif str(current_val) not in str(merged_val):  # Add only if not already present
                        merged[field] = str(merged_val) + ' + ' + str(current_val)
    
    return merged

def parse_weights(number_str: str) -> str:
    """
    Normalizes a weight string from an invoice to a standard format (e.g., '1234.565').

    This function is designed based on the rule that weights always have three decimal places.
    It intelligently detects the decimal separator (',' or '.') based on this rule.

    Args:
        number_str: The number string to parse, e.g., "1.234,565" or "1,234.565".

    Returns:
        A cleaned string in the standard 'INTEGER.DECIMAL' format.

    Raises:
        ValueError: If the number format is ambiguous or unrecognized.
    """
    if not isinstance(number_str, str):
        raise TypeError("Input must be a string.")

    s = number_str.strip()

    # If the last character is a comma or dot, it might be a dangling separator.
    if s.endswith(',') or s.endswith('.'):
        s = s[:-1]
        
    # Find the last occurrence of a comma and a dot
    last_comma_index = s.rfind(',')
    last_dot_index = s.rfind('.')

    # Case 1: The last separator is a comma, followed by exactly 3 digits.
    # This strongly indicates the EU format (e.g., "1.234,565" or "0,156").
    if last_comma_index > last_dot_index and len(s) - last_comma_index - 1 == 3:
        # Remove all dots (as thousands separators) and replace the comma with a dot.
        return s.replace('.', '').replace(',', '.')

    # Case 2: The last separator is a dot, followed by exactly 3 digits.
    # This strongly indicates the EN format (e.g., "1,234.565" or "0.635").
    if last_dot_index > last_comma_index and len(s) - last_dot_index - 1 == 3:
        # Remove all commas (as thousands separators).
        return s.replace(',', '')

    # Case 3: The number has no separators or they are not followed by 3 digits.
    # Treat it as an integer and remove all separators.
    cleaned_s = s.replace(',', '').replace('.', '')
    if cleaned_s.isdigit():
        return cleaned_s

    # If none of the above rules apply, the format is unrecognized.
    raise ValueError(f"Unrecognized or ambiguous number format: '{number_str}'")

def parse_numbers(number_str: str) -> str:
    """
    Normalize a number string into a consistent decimal format string.
    Handles both EU and EN formats and auto-detects thousands and decimal separators.
    Returns a cleaned string (not float).
    """
    number_str = number_str.strip()

    # Match EU format: 1.234,56
    if re.match(r"^\d{1,3}(\.\d{3})*,\d{1,2}$", number_str):
        return number_str.replace('.', '').replace(',', '.')

    # Match EN format: 1,234.56
    # Update to allow up to 6 decimal digits (or more)
    if re.match(r"^\d{1,3}(,\d{3})*\.\d{1,6}$", number_str):
        return number_str.replace(',', '')

    # Case: only thousands separator (EU): 2.800 → 2800
    if re.match(r"^\d{1,3}(\.\d{3})+$", number_str):
        return number_str.replace('.', '')

    # Case: only thousands separator (EN): 2,800 → 2800
    if re.match(r"^\d{1,3}(,\d{3})+$", number_str):
        return number_str.replace(',', '')

    # Case: decimal comma only: 1234,56 → 1234.56
    if re.match(r"^\d+,\d{1,2}$", number_str):
        return number_str.replace(',', '.')

    # Case: already clean like 1234.56 or 1234
    if re.match(r"^\d+(\.\d{1,2})?$", number_str):
        return number_str
    
    # Case: mixed up format like 2.988,800 → treat as 2988.8
    if re.match(r"^\d{1,3}(\.\d{3})+,\d{3}$", number_str):
        return number_str.replace('.', '').replace(',', '.')

    raise ValueError(f"Unrecognized number format: {number_str}")