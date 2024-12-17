import re 

def clean_incoterm(inco : str) -> list :
    return inco.split(' ', maxsplit=1)

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