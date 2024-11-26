from datetime import datetime
import logging
import fitz
import re

def print_json_to_file(data, filename="output.txt"):
    with open(filename, 'w') as f:
        f.write(data)

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

def normalize_number_format(s):
    """
    Converts number format by removing periods and converting commas to periods.
    
    Args:
        s (str): Input string in number format.
        
    Returns:
        str: Normalized string with commas as decimal points.
    """
    # Remove any periods and replace commas with periods for decimal
    return s.replace(".", "").replace(",", ".")

def remove_non_numeric_chars(s):
    """
    Removes all non-numeric characters from a string, leaving only numbers.
    
    Args:
        s (str): Input string.
        
    Returns:
        str: String with only numeric characters.
    """
    return re.sub(r'[^0-9.,]', '', s)

def get_abbreviation_by_country(countries, country_name):
    for entry in countries:
        if entry["country"].lower() == country_name.lower():
            return entry["abbreviation"]
    return None 

def clean_invoice_data (result, countries):

    for obj in result:
        for key, value in obj.items():
            if key == "Country of Origin: ":
                #clean and update the country
                obj[key] = get_abbreviation_by_country(countries, value)
            elif key == "Net Weight:":
                #clean and update the net weight
                obj[key] = safe_float_conversion(normalize_number_format(remove_non_numeric_chars(value)))
            elif key == "All in Price":
                #clean and update the quantity
                obj[key] = safe_int_conversion(safe_float_conversion(normalize_number_format(remove_non_numeric_chars(value))))
            elif key == "Total for the line item" or key ==  "Total freight related surcharges for the item:" or key == "Temp Reco Surchg":
                #clean and update the invoice
                price_arr = value.split(' ')
                if len(price_arr) > 1:
                    price = price_arr[0]
                    currency = price_arr[1]

                    obj[key] = [safe_float_conversion(normalize_number_format(price)), currency]

    return result              

def clean_invoice_total (value):

    price_arr = value['invoice'].split(' ')

    if len(price_arr) > 1:
        price = price_arr[0]
        currency = price_arr[1]
        return {'invoice' : [normalize_number_format(price), currency] } 
    
    return value
               
def clean_packing_list_data (result) :

    for obj in result:
        for key, value in obj.items():
            if key == "Grand Total":
                #clean and update the invoice
                arr = value.split('\n')
                if len(arr) >= 3:
                    quantitty = safe_int_conversion(safe_float_conversion(normalize_number_format(remove_non_numeric_chars(arr[0]))))
                    gross = safe_float_conversion(normalize_number_format(arr[1]))

                    obj[key] = [quantitty, gross]

    return  result           

def change_keys(data, key_map):
    """
    Recursively changes the keys in a JSON-like dictionary or list.

    :param data: The JSON-like object (dict or list) to process.
    :param key_map: A dictionary mapping old key names to new key names.
    :return: A new JSON-like object with the keys replaced.
    """
    if isinstance(data, dict):
        # Replace keys for a dictionary
        new_data = {}
        for key, value in data.items():
            new_key = key_map.get(key, key)  # Get the new key if it exists, otherwise keep the old key
            new_data[new_key] = change_keys(value, key_map)  # Recursively handle the value
        return new_data
    elif isinstance(data, list):
        # Recursively process each item in a list
        return [change_keys(item, key_map) for item in data]
    else:
        # Return the value as is if it's not a dict or list
        return data

def clean_grand_totals_in_packing_list(packinglist):
    for item in packinglist:
        # Check if 'Grand Total' exists and is a list with more than 2 elements
        if "Item Totals" in item and isinstance(item["Item Totals"], list) and len(item["Item Totals"]) > 1:
            grand_total = item["Item Totals"]

            # Add new keys for Quantity, Gross, and Net
            item["Quantity"] = grand_total[0]
            item["Gross"] = grand_total[1]

            # Remove the 'Grand Total' key
            del item["Item Totals"]

    return packinglist        

def merge_invoice_with_packing_list(invoice_data, packing_list):
    # Iterate through invoice items
    for invoice_item in invoice_data["items"]:
        # Match items by 'Batch' and 'DN Number'
        batch_number = invoice_item.get("Batch")
        dn_number = invoice_item.get("DN Number")
        
        for packing_item in packing_list:
            if (
                (packing_item.get("Batch") == batch_number
                and packing_item.get("DN Number") == dn_number) or packing_item.get("Batch") == batch_number
            ):
                # Merge non-duplicate fields from packing list into invoice item
                for key, value in packing_item.items():
                    if key not in invoice_item:  # Avoid overwriting existing keys
                        invoice_item[key] = value
                        
    return invoice_data

def calculate_totals(invoice_data):
    totals = {
        "Totals Collis": 0,
        "Totals Gross": 0.0,
        "Totals Freight Value": [0.0, ""]  # Value and currency
    }

    for item in invoice_data.get("items", []):
        # Add Collis if available
        collis = item.get("Collis")
        if collis is not None:
            totals["Totals Collis"] += safe_int_conversion(collis)

        # Add Gross if available
        gross = item.get("Gross")
        if gross is not None:
            totals["Totals Gross"] += round(safe_float_conversion(gross), 1)

        # Add Freight Item Value if available
        freight_item = item.get("Freight Item")
        if freight_item is not None and len(freight_item) > 1:
            totals["Totals Freight Value"][0] += round(safe_float_conversion(freight_item[0]), 1)
            # Set currency (assumes consistent currency across items)
            if not totals["Totals Freight Value"][1]:
                totals["Totals Freight Value"][1] = freight_item[1]

    return totals

def validate_string(input_string):
    """
    Checks if the input string is non-empty and not None.
    Returns the input string if valid, otherwise an empty string.
    """
    if input_string and isinstance(input_string, str) and input_string.strip():
        return input_string
    return ""

def safe_int_conversion(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float_conversion(value, default=0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default           
