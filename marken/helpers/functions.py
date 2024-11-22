def safe_int_conversion(value):
    try:
        return int(value)
    except ValueError:
        return None

def safe_float_conversion(value):
    try:
        return float(value)
    except ValueError:
        return None 
    
def list_to_json(values, keys):
    if len(values) != len(keys):
        raise ValueError("Values and keys lists must be of the same length")
    return dict(zip(keys, values))  

def merge_json_objects(marken_data, email_data):
    if not isinstance(marken_data, dict) or not isinstance(email_data, dict):
        raise ValueError("Both inputs must be dictionaries")
    merged_data = {}
    for key in marken_data:
        if key in email_data:
            if marken_data[key] != email_data[key]:
                merged_data[f"{key}_message"] = f"Different values for this key: marken={marken_data[key]}, email={email_data[key]}"
            else:
                merged_data[key] = marken_data[key]
        else:
            merged_data[key] = marken_data[key]
    for key in email_data:
        if key not in marken_data:
            merged_data[key] = email_data[key]
    return merged_data 

def normalize_number_format(value):
    return value.replace(".", "").replace(",", ".") 

def clean_number(value):
    value = value.replace(",", ".")
    return "".join(char for char in value if char.isdigit() or char == ".")


