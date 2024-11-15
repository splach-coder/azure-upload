import json
import os
import fitz  # PyMuPDF
import os

from sofidel.utils.number_handlers import normalize_number_format, remove_non_numeric_chars, remove_spaces_from_numeric_strings

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

def find_page_with_cmr_data(pdf_path, keywords=["Marques es num", "Nombre des colis"]):
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
        else:
            return "No relevant data found in this document."

    except Exception as e:
        return f"An error occurred: {str(e)}"

def handle_cmr_data(cmr_data):
    result = []

    for item in cmr_data:
        result.append(item.split('\n'))

    return convert_to_json_array_cmr(result)

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
    material_codes, collis, hs_codes, gross_weights = data

    # Loop through the arrays to construct each JSON object
    for i in range(len(material_codes)):
        json_object = {
            "material_code": remove_spaces_from_numeric_strings(material_codes[i]),
            "Pieces": int(remove_non_numeric_chars(collis[i])),
            "Commodity": remove_spaces_from_numeric_strings(hs_codes[i]),
            "Net": float(normalize_number_format(remove_spaces_from_numeric_strings(gross_weights[i])))
        }

        json_array.append(json_object)

    return json_array

def handle_invoice_data(cmr_data):
    result = []

    for item in cmr_data:
        material_code, qty, amount = item
        result.append([material_code, qty, normalize_number_format(amount)])

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
    # Create a dictionary to index cmr_data by (material_code, collis) for quick look-up
    cmr_dict = {
        (entry['material_code']): entry for entry in cmr_data
    }

    combined_result = []

    for table_entry in table_data:
        # Create a key tuple for lookup
        key = (table_entry['material_code'])
        
        # Look up the matching entry in cmr_data
        if key in cmr_dict:
            combined_entry = {
                **cmr_dict[key],  # Include all fields from cmr_data
                **table_entry     # Add or overwrite with fields from table_data (like 'amount')
            }
            combined_result.append(combined_entry)

    return combined_result

def combine_data_with_material_code(cmr_data, table_data):
    # Step 1: Convert string entries in table_data to dictionaries if needed
    table_data = [json.loads(entry) if isinstance(entry, str) else entry for entry in table_data]

    # Step 2: Create a dictionary to index cmr_data by material_code for quick look-up
    cmr_dict = {entry['material_code']: entry for entry in cmr_data}

    # Step 3: Initialize the combined result
    combined_result = []

    for table_entry in table_data:
        # Create a key for lookup using only material_code
        material_code = table_entry['material_code']
        
        # Look up the matching entry in cmr_data
        if material_code in cmr_dict:
            combined_entry = {
                **cmr_dict[material_code],  # Include all fields from cmr_data
                **table_entry               # Add or overwrite with fields from table_data (like 'Qty')
            }
            combined_result.append(combined_entry)

    return combined_result

def list_to_json(data_list):
    # Define the keys for each item in the list
    keys = [
        "btw", "reference_number_1", "order",
        "delivery", "address", "wagon",
        "currency", "inv date", "inv reference", "term", "total amount"
    ]
    
    # Ensure the list and keys are the same length
    if len(data_list) != len(keys):
        raise ValueError("The data list and keys list must be the same length.")
    
    # Create the JSON object by zipping keys and data_list
    result_json = dict(zip(keys, data_list))
    
    return result_json
