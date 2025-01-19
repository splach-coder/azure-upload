import re


def remove_spaces_from_numeric_strings(s):
    """
    Removes spaces from strings that represent numeric values.
    
    Args:
        s (str): Input string.
        
    Returns:
        str: String with spaces removed if it is numeric.
    """
    # Check if removing spaces gives a numeric string
    return re.sub(r'[^0-9.,]', '', s)

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
    return re.sub(r'\D', '', s)

def clean_string(input_string):
    """
    Cleans the input string by removing periods, commas, and all special characters.
    
    Parameters:
        input_string (str): The string to be cleaned.
        
    Returns:
        str: The cleaned string containing only alphanumeric characters and spaces.
    """
    # Use regex to replace non-alphanumeric characters and spaces with an empty string
    cleaned_string = re.sub(r'[^a-zA-Z0-9 ]', '', input_string)
    return cleaned_string

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

def filter_numeric_strings(input_list):
    def is_number(s):
        s = s.strip()  # Remove leading/trailing whitespace
        # Exclude strings that are purely alphabetic (like 'g', 'abc')
        if re.fullmatch(r'[a-zA-Z]+', s):
            return False
        # Allow numbers, decimals, commas, and optional "NR"
        return True
    
    # Process the list of lists
    cleaned_list = []
    for sublist in input_list:
        filtered_sublist = [item for item in sublist if is_number(item)]
        cleaned_list.append(filtered_sublist)
    
    return cleaned_list

def normalize_number_format_global_weight(s):
    """
    Converts number format by removing the first period if there are multiple periods
    and converting commas to periods.
    
    Args:
        s (str): Input string in number format.
        
    Returns:
        str: Normalized string with commas as decimal points and handling of periods.
    """
    # Count the number of periods in the string
    period_count = s.count('.')
    
    if period_count > 1:
        # Remove the first period
        first_period_index = s.find('.')
        s = s[:first_period_index] + s[first_period_index + 1:]
    
    # Replace commas with periods for decimal
    return s.replace(",", ".")    