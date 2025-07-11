import logging
import re

import fitz

def clean_data_from_texts_that_above_value(text):
    """
    Cleans the input text by removing any text that appears above a specified value.
    The value is defined as a string that contains only digits, commas, or periods.
    """
    lines = text.split('\n')
    if lines and len(lines) > 1:
        return lines[1].strip()
    return text

def clean_VAT(VAT_number):
    pattern = r'\w{2}\s?\d{10}'
    match = re.search(pattern, VAT_number)
    if match:
        return match.group().replace(" ", "").upper()
    else:
        return ""

def get_abbreviation_by_country(countries, country_name):
    for entry in countries:
        if entry["country"].lower() == country_name.lower():
            return entry["abbreviation"]
    return country_name   

def is_valid_number(s):
    # Regex pattern for a valid number (integer or float)
    pattern = r'^[0-9.,]*$'  # Matches integers and floats, including negative numbers
    return bool(re.match(pattern, s))

def abbr_countries_in_items(result, countries):
    for item in result:
        origin = item.get("Origin", "").split('\n')
        if len(origin) > 1:
            for itm in origin:
                if len(itm) < 2:
                    origin.remove(itm)
        origin = ''.join(origin)            
        item["Origin"] = get_abbreviation_by_country(countries, origin)
    return result

def normalize_numbers(s):
    return s.replace(".", "").replace(",", ".")

def safe_float_conversion(s):
    try:
        return float(s)
    except ValueError:
        return 0.0

def safe_int_conversion(s):
    try:
        return int(s)
    except ValueError:
        return 0

def normalize_the_items_numbers(result):
    for item in result:
        item["Net"] = safe_float_conversion(normalize_numbers(item["Net"]))
        item["Value"] = safe_float_conversion(normalize_numbers(item["Value"]))
        item["Quantity"] = safe_int_conversion(normalize_numbers(item["Quantity"]))
    return result

def add_inv_date_to_items(result, inv_date):
    for item in result:
        item["Inv No"] = inv_date
    return result

def normalize_the_totals_type(result):
    for key, value in result.items():
        if key == "Weight" : result[key] = safe_float_conversion(normalize_numbers(value))
        if key == "Total Value" : result[key] = safe_float_conversion(normalize_numbers(value))
        if key == "Quantity" : result[key] = safe_int_conversion(normalize_numbers(value))
        if key == "Package" : result[key] = safe_int_conversion(normalize_numbers(value))
        
    return result


def merge_pdf_data(pdf_data_list):
    """
    Merges a list of dictionaries containing data extracted from PDFs.
    Fields with differing values are concatenated with '+', except for 'items' which are appended.
    """
    if not pdf_data_list:
        return {}

    # Start with the first dictionary as the base
    merged_data = pdf_data_list[0].copy()
    
    for data in pdf_data_list[1:]:
        for key, value in data.items():
            if key == "items":  # Special handling for 'items'
                merged_data[key].extend(value) 
            elif isinstance(value, list):  # Handle lists (e.g., Address, Terms)
                if len(merged_data[key]) == len(value):
                    merged_data[key] = merged_data[key]
                else:
                    merged_data[key] = ['', '', '', '', '']  # Assign an empty list if lengths are not the same
            elif isinstance(value, (int, float)):  # Handle numerical fields
                if value:
                    merged_data[key] += value
            else:  # Handle strings or other types
                if merged_data[key] != value:
                    merged_data[key] = f"{merged_data[key]}+{value}" if merged_data[key] else value

    # Remove duplicates from 'items' (if necessary)
    merged_data["items"] = [dict(t) for t in {tuple(d.items()) for d in merged_data["items"]}]

    return merged_data


def handle_terms_into_arr(s):
    if s is None:
        return s
    
    arr = s.split(" ", 1)
    
    if len(arr) == 1:
        return s
    
    return arr

def check_invoice_in_pdf(pdf_path):
    try:
        # Open the PDF file
        document = fitz.open(pdf_path)
        
        # Check if the document has at least one page
        if document.page_count > 0:
            # Extract text from the first page
            first_page = document[0]
            text = first_page.get_text()
            
            # Check if "INVOICE" is in the extracted text
            if "INVOICE" in text.upper() and "(original)".upper() in text.upper() :  # Convert to uppercase for case-insensitive comparison
                return True
        
        return False  # Return False if "INVOICE" is not found or if there are no pages
    except Exception as e:
        print(f"An error occurred: {e}")
        return False  # Return False in case of any error
