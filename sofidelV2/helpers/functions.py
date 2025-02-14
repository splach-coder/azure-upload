import json
import re
import os
import fitz  # PyMuPDF
import os

from sofidel.utils.number_handlers import filter_numeric_strings, normalize_number_format, remove_non_numeric_chars, remove_spaces_from_numeric_strings, safe_float_conversion, safe_int_conversion

def detect_pdf_type(pdf_path):
    try:
        # Get the file name from the path
        file_name = os.path.basename(pdf_path)
        
        # Check if "CMR" is in the file name (case-insensitive)
        if "CMR" in file_name.upper():
            return "CMR"
        return "INVOICE"
        
    except Exception as e:
        return f"An error occurred: {str(e)}"

def find_page_with_cmr_data(pdf_path, keywords=["Marques es num", "Nombre des colis", "Art der Verpacku", "Nature de la", "No statistique"]):
    try:
        # Get the file name from the path
        file_name = os.path.basename(pdf_path)
        
        # Check if "CMR" is in the file name (case-insensitive)
        if "CMR" not in file_name.upper():
            return "This file is not identified as a CMR document."

        # Open the PDF file
        pdf_document = fitz.open(pdf_path)
        
        # Ensure the PDF has at least 1 page
        if len(pdf_document) < 1:
            return "The PDF is empty or has no pages."

        # Search for pages containing all the keywords
        pages_with_data = []
        for page_number in range(len(pdf_document)):
            page = pdf_document[page_number]
            page_text = page.get_text("text")

            # Check if all keywords are found on this page
            if any(keyword in page_text for keyword in keywords):
                pages_with_data.append(page_number + 1)  # Page numbers are 1-based
            
        if pages_with_data:
            return pages_with_data
        else:
            return "No relevant data found in this document."

    except Exception as e:
        return f"An error occurred: {str(e)}"

def find_page_with_cmr_data_any(pdf_path, keywords=["Marques es num", "Nombre des colis"]):
    try:
        # Get the file name from the path
        file_name = os.path.basename(pdf_path)
        
        # Check if "CMR" is in the file name (case-insensitive)
        if "CMR" not in file_name.upper():
            return "This file is not identified as a CMR document."

        # Open the PDF file
        pdf_document = fitz.open(pdf_path)
        
        # Ensure the PDF has at least 1 page
        if len(pdf_document) < 1:
            return "The PDF is empty or has no pages."

        # Search for pages containing all the keywords
        pages_with_data = []
        for page_number in range(len(pdf_document)):
            page = pdf_document[page_number]
            page_text = page.get_text("text")

            # Check if all keywords are found on this page
            if any(keyword in page_text for keyword in keywords):
                pages_with_data.append(page_number + 1)  # Page numbers are 1-based
            
        if pages_with_data:
            return pages_with_data
        else:
            return "No relevant data found in this document."

    except Exception as e:
        return f"An error occurred: {str(e)}"

def find_page_with_cmr_data_fallback(pdf_path, keywords=["Marques es num", "Nombre des colis"]):
    try:
        # Get the file name from the path
        file_name = os.path.basename(pdf_path)
        
        # Check if "CMR" is in the file name (case-insensitive)
        if "CMR" not in file_name.upper():
            return "This file is not identified as a CMR document."

        # Open the PDF file
        pdf_document = fitz.open(pdf_path)
        
        # Ensure the PDF has at least 1 page
        if len(pdf_document) < 1:
            return "The PDF is empty or has no pages."

        # Search for pages containing all the keywords
        pages_with_data = []
        for page_number in range(len(pdf_document)):
            page = pdf_document[page_number]
            page_text = page.get_text("text")

            # Check if all keywords are found on this page
            if all(keyword in page_text for keyword in keywords):
                pages_with_data.append(page_number + 1)  # Page numbers are 1-based
            
        if pages_with_data:
            return pages_with_data
        elif find_page_with_cmr_data_any(pdf_path, keywords=keywords):
            return find_page_with_cmr_data_any(pdf_path, keywords=keywords)
        else:
            return "No relevant data found in this document."

    except Exception as e:
        return f"An error occurred: {str(e)}"

def handle_cmr_data(cmr_data):
    result = []

    for item in cmr_data:
        result.append(item.split('\n'))

    result = filter_numeric_strings(result)

    return convert_to_json_array_cmr(result)

def clean_and_normalize_sublists(list_of_lists):
    cleaned_list = []
    max_length = 0

    for sublist in list_of_lists:
        cleaned_sublist = [item for item in sublist if any(char.isdigit() for char in item)]
        cleaned_list.append(cleaned_sublist)
        max_length = max(max_length, len(cleaned_sublist))

    for sublist in cleaned_list:
        while len(sublist) < max_length:
            sublist.append('0')

    return cleaned_list

def convert_to_json_array_cmr(data):
    """
    Converts a 2D array into a list of JSON objects, mapping each sub-array element to specific fields.
    
    Args:
        data (list of list of str): Input 2D array with each sub-array containing items.
        
    Returns:
        list of dict: List of JSON objects with keys 'material_code', 'collis', 'hs', and 'gross_weight'.
    """
    json_array = []
    # Unpack sub-arrays for each attribute (assuming they are in the correct order)
    data = clean_and_normalize_sublists(data)
    material_codes, collis, hs_codes, gross_weights = clean_and_normalize_sublists(data)

    # Loop through the arrays to construct each JSON object
    for i in range(len(material_codes)):
        json_object = {
            "material_code": remove_spaces_from_numeric_strings(material_codes[i]),
            "Pieces": safe_int_conversion(remove_non_numeric_chars(collis[i])),
            "Commodity": remove_spaces_from_numeric_strings(hs_codes[i]),
            "Net": safe_float_conversion(normalize_number_format(remove_spaces_from_numeric_strings(gross_weights[i])))
        }

        json_array.append(json_object)

    return json_array

def handle_invoice_data(cmr_data):
    result = []

    for item in cmr_data:
        material_code, qty, amount = item
        result.append([material_code, normalize_number_format(qty), normalize_number_format(amount)])

    return convert_to_json_array_invoice(result)

def convert_to_json_array_invoice(data):
    """
    Converts a 2D array into a list of JSON objects, mapping each sub-array element to specific fields.
    
    Args:
        data (list of list of str): Input 2D array with each sub-array containing items.
        
    Returns:
        list of dict: List of JSON objects with keys 'material_code', 'collis', 'hs', and 'gross_weight'.
    """
    json_array = []

    # Loop through the arrays to construct each JSON object
    for item in data:
        json_object = {
            "material_code": item[0],
            "Pieces": float(item[1]),
            "Invoice value": float(item[2])
        }

        json_array.append(json_object)

    return json_array

def combine_data_with_material_code_collis(cmr_data, table_data):
    """
    Enrich table_data with additional fields from cmr_data based on matching material_code or collis.
    
    Parameters:
        cmr_data (list): List of dictionaries containing CMR data.
        table_data (list): List of dictionaries containing table data.
        
    Returns:
        list: Updated table_data with fields from CMR data added when matches are found.
    """
    # Step 1: Create a dictionary to index cmr_data by material_code and collis
    cmr_dict = {}
    for entry in cmr_data:
        # Use material_code and collis as keys if they exist
        key_material_code = entry.get('material_code')
        key_collis = entry.get('Pieces')
        if key_material_code:
            cmr_dict[key_material_code] = entry
        if key_collis:
            cmr_dict[key_collis] = entry

    enriched_result = []

    for table_entry in table_data:
        # Attempt to match by material_code or collis
        material_code = table_entry.get('material_code')
        collis = table_entry.get('Pieces')

        # Check if either material_code or collis exists in the cmr_dict
        matching_entry = cmr_dict.get(material_code) or cmr_dict.get(collis)

        if matching_entry:
            # Add only the fields from matching_entry that are not in table_entry
            enriched_entry = {
                **table_entry,       # Keep all fields from table_data
                **{k: v for k, v in matching_entry.items() if k not in table_entry}  # Add missing fields from CMR
            }
        else:
            # If no match is found, keep the table_entry as is
            enriched_entry = table_entry
        
        enriched_result.append(enriched_entry)

    return enriched_result

def combine_data_with_material_code_or_pieces(cmr_data, table_data):
    """
    Combine data from cmr_data and table_data based on matching material_code or Pieces.
    This function keeps cmr_data entries unchanged unless table_data provides additional fields
    not already in the cmr_data entry.
    
    Parameters:
        cmr_data (list): List of dictionaries containing CMR data.
        table_data (list): List of dictionaries (or JSON strings) containing table data.
        
    Returns:
        list: List of enriched cmr_data entries.
    """
    # Step 1: Convert string entries in table_data to dictionaries if needed
    table_data = [json.loads(entry) if isinstance(entry, str) else entry for entry in table_data]

    # Step 2: Create a dictionary to index cmr_data by both material_code and Pieces for quick look-up
    cmr_dict = {}
    for entry in cmr_data:
        key_material_code = entry.get('material_code')
        key_pieces = entry.get('Pieces')
        if key_material_code:
            cmr_dict[key_material_code] = entry
        if key_pieces:
            cmr_dict[key_pieces] = entry

    # Step 3: Initialize the combined result with CMR data entries
    combined_result = []

    for table_entry in table_data:
        # Attempt to match by material_code or Pieces
        material_code = table_entry.get('material_code')
        pieces = table_entry.get('Pieces')
        
        # Check if either material_code or Pieces exists in the cmr_dict
        matching_entry = cmr_dict.get(material_code) or cmr_dict.get(pieces)
        
        if matching_entry:
            # Create a copy of the matching_entry to keep the original cmr_data unchanged
            combined_entry = matching_entry.copy()

            # Add missing fields from table_entry to combined_entry
            for key, value in table_entry.items():
                if key not in combined_entry:  # Add only missing fields
                    combined_entry[key] = value

            combined_result.append(combined_entry)

    return combined_result

def list_to_json(data_list):
    # Define the keys for each item in the list
    keys = [
        "btw",  "order",
        "delivery", "address", "wagon",
        "currency", "inv date", "inv reference", "term", "total amount"
    ]
    
    # Ensure the list and keys are the same length
    if len(data_list) != len(keys):
        raise ValueError("The data list and keys list must be the same length.")
    
    # Create the JSON object by zipping keys and data_list
    result_json = dict(zip(keys, data_list))
    
    return result_json

def validate_data(data):
    try:
        # Extracting data from the dictionary
        items = data.get("items", [])
        total_pallets = int(data.get("total pallets", 0))
        total_amount = float(data.get("total amount", "0").replace(".", "").replace(",", "."))
        
        # Calculating sums
        sum_collis = sum(item.get("Collis", 0) for item in items)
        sum_invoice_value = sum(item.get("Invoice value", 0) for item in items)
        
        # Validation
        pallets_match = sum_collis == total_pallets
        amount_match = round(sum_invoice_value, 2) == round(total_amount, 2)
        
        # Preparing the message
        if pallets_match and amount_match:
            return "Validation successful! The total pallets and total amount match the items data."
        else:
            message = "Validation failed:"
            if not pallets_match:
                message += f"\n- Total pallets mismatch: Expected {total_pallets}, but calculated {sum_collis}."
            if not amount_match:
                message += f"\n- Total amount mismatch: Expected {total_amount}, but calculated {round(sum_invoice_value, 2)}."
            return message
    except Exception as e:
        return f"An error occurred during validation: {e}"
    
def extract_id_from_string(input_string):
    # Use a regular expression to find a 7-digit number in the string
    match = re.search(r'\d{7}', input_string)
    if match:
        # Return the ID as an integer
        return int(match.group())
    else:
        # Return None if no ID is found
        return None

def transform_data(items):
    """
    Transform a list of dictionaries into separate arrays for each field,
    handling newline-separated values by splitting them.
    Only includes HS codes and Gross Weights when they exist.
    
    Args:
        items (list): List of dictionaries containing product information
        
    Returns:
        tuple: Four lists containing product codes, pieces, HS codes, and gross weights
    """
    product_codes = []
    pieces = []
    hs_codes = []
    gross_weights = []
    
    # First pass: collect all product codes and pieces
    for item in items:
        product_codes.append(item.get("Product Code", ""))
        pieces.append(item.get("Pieces", ""))
    
    # Second pass: collect only existing HS codes and Gross Weights
    for item in items:
        if "HS code" in item:
            codes = item["HS code"].split("\n")
            hs_codes.extend(codes)
            
        if "Gross Weight" in item:
            weights = item["Gross Weight"].split("\n")
            gross_weights.extend(weights)
            
    return [product_codes, pieces, hs_codes, gross_weights]

def arrays_to_objects(arrays):
    """
    Convert parallel arrays into a list of standardized objects.
    Takes corresponding elements from each array to form complete objects.
    
    Args:
        arrays (list): List of lists containing [product_codes, pieces, hs_codes, gross_weights]
    
    Returns:
        list: List of dictionaries with standardized structure
    """
    product_codes, pieces, hs_codes, gross_weights = arrays
    result = []
    
    # Use the length of product codes as base since it's guaranteed to have all items
    for i in range(len(product_codes)):
        # Only create object if we have corresponding HS code and Gross Weight
        obj = {
            "Product Code": product_codes[i],
            "Pieces": pieces[i],
            "HS code": hs_codes[i],
            "Gross Weight": gross_weights[i]
        }
        result.append(obj)
    
    return result

def transform_items_collis(items):
    """
    Transform a list of dictionaries into separate arrays for each field,
    handling newline-separated values by splitting them.
    Only includes HS codes and Gross Weights when they exist.
    
    Args:
        items (list): List of dictionaries containing product information
        
    Returns:
        tuple: Four lists containing product codes, pieces, HS codes, and gross weights
    """
    product_codes = []
    Collis = []
    

    # Second pass: collect only existing HS codes and Gross Weights
    for item in items:
        if "Product Code" in item:
            codes = item["Product Code"].split("\n")
            product_codes.extend(codes)
            
        if "Collis" in item:
            weights = item["Collis"].split("\n")
            Collis.extend(weights)
            
    return [product_codes, Collis]

def arrays_items_collis(arrays):
    """
    Convert parallel arrays into a list of standardized objects.
    Takes corresponding elements from each array to form complete objects.
    
    Args:
        arrays (list): List of lists containing [product_codes, pieces, hs_codes, gross_weights]
    
    Returns:
        list: List of dictionaries with standardized structure
    """
    product_codes, Collis = arrays
    result = []
    
    # Use the length of product codes as base since it's guaranteed to have all items
    if len(product_codes) == len(Collis):
        for i in range(len(product_codes)):
            # Only create object if we have corresponding HS code and Gross Weight
            obj = {
                "Product Code": product_codes[i],
                "Collis": Collis[i],
            }
            result.append(obj)
    else :
        for i in range(len(product_codes)):
            # Only create object if we have corresponding HS code and Gross Weight
            obj = {
                "Product Code": product_codes[i],
                "Collis": 0,
            }
            result.append(obj)

    
    return result

