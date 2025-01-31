import json
import re
from bs4 import BeautifulSoup

def clean_incoterm(inco : str) -> list :
    return inco.split(' ', maxsplit=1)

def clean_Origin(value : str) -> str :
    return value.replace("Origin:", "")

def clean_HS_code(value : str) -> str :
    return value.replace(",", "")

def normalize_numbers(number_str : str) -> float:
    """
    Normalize a number string to a consistent float format.
    :param number_str: A string representing a number (e.g., "3.158,6" or "28,158.23").
    :return: A float representing the normalized number.
    """
    normalized = ""
    # Handle comma as decimal separator
    if re.match(r"^\d{1,3}(\.\d{3})*,\d{1,2}$", number_str):
        # Replace dots (thousands separator) with nothing, replace comma (decimal) with a dot
        normalized = number_str.replace('.', '').replace(',', '.')
    # Handle dot as decimal separator
    elif re.match(r"^\d{1,3}(,\d{3})*\.\d{1,2}$", number_str):
        # Replace commas (thousands separator) with nothing
        normalized = number_str.replace(',', '')
    
    return normalized

def clean_number_from_chars(value: str) -> str:
    # Use regex to keep only digits, commas, and periods
    cleaned = re.sub(r'[^\d.,]', '', value)
    return cleaned

def clean_customs_code(value : str) -> str:
    return value.replace(')', '')

def safe_int_conversion(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 0

def safe_float_conversion(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.00  
    
def extract_and_clean(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    data = soup.get_text()
    
    return data    

def extract_container_number(text):
    """
    Extract the container number from a given text.
    The format is: Two characters (letters), optional space, four numbers.
    
    Args:
        text (str): The input text.
    
    Returns:
        str or None: The container number if found, otherwise None.
    """
    pattern = r"\b([A-Za-z]{4}\d{4})\b"
    match = re.search(pattern, text)
    return match.group(1) if match else ""

def extract_Exitoffice(text):
    """
    Extract the container number from a given text.
    The format is: Two characters (letters), optional space, four numbers.
    
    Args:
        text (str): The input text.
    
    Returns:
        str or None: The container number if found, otherwise None.
    """
    pattern = r"\b([A-Za-z]{2}\s?\d{6})\b"
    match = re.search(pattern, text)
    return match.group(1) if match else ""

def merge_json_objects(json_objects):
    # Initialize the output with the first object
    merged_object = json_objects[0].copy()

    # Function to handle value joining only if the values differ
    def join_values_if_diff(key, merged_obj, obj_list):
        values = [obj.get(key) for obj in obj_list if key in obj and obj[key] is not None]
        if values:
            # Only join if the values are different
            unique_values = set(values)
            if len(unique_values) > 1:  # Values are different
                merged_obj[key] = '+'.join(unique_values)
            else:
                merged_obj[key] = values[0]

    # Iterate over the other JSON objects
    for obj in json_objects[1:]:
        # Join values for the specified fields with "+" if different
        join_values_if_diff("Inv Reference", merged_object, [merged_object, obj])
        join_values_if_diff("Other Ref", merged_object, [merged_object, obj])  

        # Sum fields like Total, Freight, and Gross weight Total
        if "Total" in obj and obj["Total"] is not None:
            if "Total" in merged_object and merged_object["Total"] is not None:
                merged_object["Total"][0] += obj["Total"][0]
            else:
                merged_object["Total"] = obj["Total"]
                
        # Sum fields like Total, Freight, and Gross weight Total
        if "Total pallets" in obj and obj["Total pallets"] is not None:
            if "Total pallets" in merged_object and merged_object["Total pallets"] is not None:
                merged_object["Total pallets"][0] += obj["Total pallets"][0]
            else:
                merged_object["Total pallets"] = obj["Total pallets"]

        if "Freight" in obj and obj["Freight"] is not None:
            if "Freight" in merged_object and merged_object["Freight"] is not None:
                merged_object["Freight"][0] += obj["Freight"][0]
            else:
                merged_object["Freight"] = obj["Freight"]

        if "Gross weight Total" in obj and obj["Gross weight Total"] is not None:
            if "Gross weight Total" in merged_object and merged_object["Gross weight Total"] is not None:
                merged_object["Gross weight Total"] += obj["Gross weight Total"]
            else:
                merged_object["Gross weight Total"] = obj["Gross weight Total"]

        # Append Items items
        if "Items" in obj and obj["Items"] is not None:
            if "Items" not in merged_object or merged_object["Items"] is None:
                merged_object["Items"] = []
            merged_object["Items"].extend(obj["Items"])

        # Copy values for Address, Incoterm, and Origin (ensure to not overwrite)
        for key in ["Incoterm", "Address"]:
            if key in obj and obj[key] is not None and (key not in merged_object or merged_object[key] is None):
                merged_object[key] = obj[key]

    return merged_object
