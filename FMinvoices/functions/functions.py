import re
from bs4 import BeautifulSoup


def clean_incoterm(inco : str) -> list :
    return inco.split(' ', maxsplit=1)

def clean_Origin(value : str) -> str :
    return value.replace("Origin:", "").replace("d'origine:", "")

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

def normalize_numbers_gross(number_str: str) -> float:
    """
    Normalize a number string to a consistent float format.
    :param number_str: A string representing a number (e.g., "3.158,6" or "28,158.23").
    :return: A float representing the normalized number.
    """
    # Handle comma as decimal separator
    if re.match(r"^\d{1,3}(\.\d{3})*,\d{1,2}$", number_str):
        # Replace dots (thousands separator) with nothing, replace comma (decimal) with a dot
        normalized = number_str.replace('.', '').replace(',', '.')
    # Handle dot as decimal separator
    elif re.match(r"^\d{1,3}(,\d{3})*\.\d{1,2}$", number_str):
        # Replace commas (thousands separator) with nothing
        normalized = number_str.replace(',', '')
    # Handle cases with only thousands separator (no decimal part)
    elif re.match(r"^\d{1,3}(\.\d{3})*$", number_str):
        # Replace dots (thousands separator) with nothing
        normalized = number_str.replace('.', '')
    elif re.match(r"^\d{1,3}(,\d{3})*$", number_str):
        # Replace commas (thousands separator) with nothing
        normalized = number_str.replace(',', '')
    else:
        # If the format is not recognized, return None
        return None

    try:
        return float(normalized)
    except ValueError:
        return None

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
        join_values_if_diff("Inv Ref", merged_object, [merged_object, obj])

        # Sum fields like Total, Freight, and Gross weight Total
        if "Total Price" in obj and obj["Total Price"] is not None:
            if "Total Price" in merged_object and merged_object["Total Price"] is not None:
                merged_object["Total Price"] += obj["Total Price"]
            else:
                merged_object["Total Price"] = obj["Total Price"]
                
        # Sum fields
        if "Total Collis" in obj and obj["Total Collis"] is not None:
            if "Total Collis" in merged_object and merged_object["Total Collis"] is not None:
                merged_object["Total Collis"] += obj["Total Collis"]
            else:
                merged_object["Total Collis"] = obj["Total Collis"]

        if "Total Gross" in obj and obj["Total Gross"] is not None:
            if "Total Gross" in merged_object and merged_object["Total Gross"] is not None:
                merged_object["Total Gross"] += obj["Total Gross"]
            else:
                merged_object["Total Gross"] = obj["Total Gross"]

        if "Total Net" in obj and obj["Total Net"] is not None:
            if "Total Net" in merged_object and merged_object["Total Net"] is not None:
                merged_object["Total Net"] += obj["Total Net"]
            else:
                merged_object["Total Net"] = obj["Total Net"]

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

def format_references(reference_str):
    # Extract and sort unique numbers
    refs = sorted(set(map(int, re.findall(r'\d+', reference_str))))  
    base = str(refs[0])[:-2]  # Take the base part of the first number
    formatted_refs = [str(refs[0])]  # Start with the full first reference

    for i in range(1, len(refs)):
        current = str(refs[i])
        prev = str(refs[i - 1])

        # Check if only the last two digits change (same base)
        if current[:-2] == prev[:-2]:
            formatted_refs.append(current[-2:])  # Add only last two digits
        else:
            formatted_refs.append("/" + current)  # Start a new base

    return "/".join(formatted_refs)  # Join formatted parts