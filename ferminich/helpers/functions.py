def get_abbreviation_by_country(countries, country_name):
    for entry in countries:
        if entry["country"].lower() == country_name.lower():
            return entry["abbreviation"]
    return country_name

def get_currency_abbr(text):
    return text.split('-', 1)[0]

def get_inco_arr(text):
    return text.split('-', 1)

def safe_float_conversion(value):
    try:
        return float(value)
    except ValueError:
        return 0

def safe_int_conversion(value):
    try:
        return int(value)
    except ValueError:
        return 0
    
def normalise_number(value):
    return value.replace(',', '')

def combine_invoices(data):
    """
    Combines multiple invoice dictionaries into a single JSON object.

    Parameters:
        data (list): A list of dictionaries representing invoice data.

    Returns:
        dict: A single combined JSON object.
    """
    if not data:
        return {}

    combined_data = data[0].copy()  # Start with a copy of the first invoice
    combined_data["Inv Ref"] = " + ".join([invoice["Inv Ref"] for invoice in data])  # Combine Inv Ref
    combined_data["items"] = []  # Initialize an empty list for items
    combined_data["total"] = [data[0]["Currency"], 0]  # Initialize total with currency and sum

    # Process items and total
    for invoice in data:
        combined_data["items"].extend(invoice["items"])  # Add items to the array
        combined_data["total"][1] += invoice["total"][1]  # Sum up the total

    return combined_data
 
def remove_non_numeric_chars(text):
    return ''.join(char for char in text if char.isdigit() or char in ['.', ','])   

def clean_invoice_text(invoice_text):
    # Define the line of underscores to detect
    line_of_underscores = "\n_____________________________________________________________________________________________________________________"
    
    # Remove the line of underscores and the first newline character
    cleaned_text = invoice_text.replace(line_of_underscores, "")
    
    # Remove the first newline character if it exists
    if cleaned_text.startswith("\n"):
        cleaned_text = cleaned_text[1:]
    
    return cleaned_text