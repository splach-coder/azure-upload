from datetime import datetime
import fitz

def clean_incoterm(incoterm):
    if not incoterm:
        return ["", ""]
    
    #split the incoterm by comma
    incoterm_parts = incoterm.split(",")
    
    #each part should be stripped of leading and trailing spaces
    incoterm_parts = [part.strip() for part in incoterm_parts]
    
    return incoterm_parts

def clean_customs_code(value : str) -> str:
    return value.replace(')', '').replace(' ', '').replace(",", "")

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

def safe_int_conversion(value: str) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

def safe_float_conversion(value: str) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def safe_lower(var):
    """
    Returns the lower-case version of var if it is not None,
    otherwise returns an empty string.
    """
    if var is None:
        return ""
    return var.lower()

def normalize_number(value: str) -> str:
    return value.replace(" ", "").replace(".", "").replace(",", ".")  

def merge_factuur_objects(factuur_array):
    """
    Merge multiple factuur objects into a single consolidated object.
    
    Args:
        factuur_array (list): Array of factuur objects to merge
        
    Returns:
        dict: Merged factuur object
    """
    if not factuur_array:
        return {}
    
    if len(factuur_array) == 1:
        return factuur_array[0]
    
    # Start with the first object as base
    merged = factuur_array[0].copy()
    
    # Fields that should be summed (numeric fields)
    numeric_fields = [
        "Total Gross", "Total Net", "Total Value", "Total Pallets"
    ]
    
    # Fields that should be concatenated if different (text fields)
    text_fields = [
        "Inv Number", "Other Ref", "Truck Nbr", "Container", "Seal", "Filename"
    ]
    
    # Fields that should remain the same (use first object's value)
    # These are typically consistent across related invoices
    consistent_fields = [
        "Address", "Cust Nbr", "Incoterm", "Inv Date", "Rex Number", 
        "VAT", "Customs Code", "Currency", "File Type", "Reference"
    ]
    
    # Initialize merged Items array
    merged["Items"] = []
    
    # Process each factuur object
    for factuur in factuur_array:
        # Add all items to the merged items array
        if "Items" in factuur and factuur["Items"]:
            merged["Items"].extend(factuur["Items"])
    
    # Process remaining objects (skip first one since it's our base)
    for i in range(1, len(factuur_array)):
        current_factuur = factuur_array[i]
        
        # Handle numeric fields - sum them up
        for field in numeric_fields:
            if field in current_factuur and field in merged:
                current_val = current_factuur[field] if current_factuur[field] is not None else 0
                merged_val = merged[field] if merged[field] is not None else 0
                merged[field] = merged_val + current_val
        
        # Handle text fields - concatenate if different
        for field in text_fields:
            if field in current_factuur and field in merged:
                current_val = current_factuur[field]
                merged_val = merged[field]
                
                # Skip if either is None or empty
                if not current_val or not merged_val:
                    continue
                    
                # If values are different, concatenate with ' + '
                if str(current_val).strip() != str(merged_val).strip():
                    if ' + ' not in str(merged_val):  # Avoid duplicate concatenation
                        merged[field] = str(merged_val) + ' + ' + str(current_val)
                    elif str(current_val) not in str(merged_val):  # Add only if not already present
                        merged[field] = str(merged_val) + ' + ' + str(current_val)
    
    return merged


# Example usage function
def test_merge_function():
    """Test function to demonstrate the merge functionality"""
    
    # Your sample data
    sample_data = [
        {
            "Address": [
                "WÜRTH NORGE A/S",
                "MORTEVEIEN HOLUM SKOG 12",
                "HAGAN",
                "1481",
                "NO"
            ],
            "Cust Nbr": "1003498",
            "Incoterm": [
                "FCA",
                "Turnhout"
            ],
            "Inv Date": "2025-06-04",
            "Inv Number": "1801821467",
            "Other Ref": "97238226",
            "Rex Number": "BE1104),",
            "Total Gross": 3571.776,
            "Total Net": 2811.744,
            "VAT": "BE0404914028",
            "Total Value": 10108.8,
            "Items": [
                {
                    "HS Code": "32141010",
                    "COO": "BE",
                    "Gross Weight": 3571.776,
                    "Net Weight": 2811.744,
                    "Value": 10108.8,
                    "Inv Number": "1801821467",
                    "Customs Code": "BE1104",
                    "Currency": "EUR"
                }
            ],
            "Total Pallets": None,
            "Truck Nbr": None,
            "Container": None,
            "Seal": None,
            "Customs Code": "BE1104",
            "Currency": "EUR",
            "File Type": "export",
            "Reference": "6100027423",
            "Filename": "factuur 6100027423 - 87870092 Wurth NO.pdf"
        },
        {
            "Address": [
                "WÜRTH NORGE A/S",
                "MORTEVEIEN HOLUM SKOG 12",
                "HAGAN",
                "1481",
                "NO"
            ],
            "Cust Nbr": "1003498",
            "Incoterm": [
                "FCA",
                "Turnhout"
            ],
            "Inv Date": "2025-06-04",
            "Inv Number": "1801821468",
            "Other Ref": "97238229",
            "Rex Number": "BE1104),",
            "Total Gross": 1785.888,
            "Total Net": 1405.872,
            "VAT": "BE0404914028",
            "Total Value": 5054.4,
            "Items": [
                {
                    "HS Code": "32141010",
                    "COO": "BE",
                    "Gross Weight": 1785.888,
                    "Net Weight": 1405.872,
                    "Value": 5054.4,
                    "Inv Number": "1801821468",
                    "Customs Code": "BE1104",
                    "Currency": "EUR"
                }
            ],
            "Total Pallets": None,
            "Truck Nbr": None,
            "Container": None,
            "Seal": None,
            "Customs Code": "BE1104",
            "Currency": "EUR",
            "File Type": "export",
            "Reference": "6100027423",
            "Filename": "factuur 6100027423 - 87870086 Wurth NO.pdf"
        },
        {
            "Address": [
                "WÜRTH NORGE A/S",
                "MORTEVEIEN HOLUM SKOG 12",
                "HAGAN",
                "1481",
                "NO"
            ],
            "Cust Nbr": "1003498",
            "Incoterm": [
                "FCA",
                "Turnhout"
            ],
            "Inv Date": "2025-06-04",
            "Inv Number": "1801821466",
            "Other Ref": "97238216",
            "Rex Number": "BE1104),",
            "Total Gross": 1785.888,
            "Total Net": 1405.872,
            "VAT": "BE0404914028",
            "Total Value": 5054.4,
            "Items": [
                {
                    "HS Code": "32141010",
                    "COO": "BE",
                    "Gross Weight": 1785.888,
                    "Net Weight": 1405.872,
                    "Value": 5054.4,
                    "Inv Number": "1801821466",
                    "Customs Code": "BE1104",
                    "Currency": "EUR"
                }
            ],
            "Total Pallets": None,
            "Truck Nbr": None,
            "Container": None,
            "Seal": None,
            "Customs Code": "BE1104",
            "Currency": "EUR",
            "File Type": "export",
            "Reference": "6100027423",
            "Filename": "factuur 6100027423 - 87870089 Wurth NO.pdf"
        }
    ]
    
    # Test the merge function
    merged_result = merge_factuur_objects(sample_data)
    
    print("Merged Result:")
    print(f"Total Gross: {merged_result['Total Gross']}")  # Should be sum of all
    print(f"Total Net: {merged_result['Total Net']}")      # Should be sum of all
    print(f"Total Value: {merged_result['Total Value']}")  # Should be sum of all
    print(f"Inv Numbers: {merged_result['Inv Number']}")   # Should be concatenated
    print(f"Other Refs: {merged_result['Other Ref']}")     # Should be concatenated
    print(f"Filenames: {merged_result['Filename']}")       # Should be concatenated
    print(f"Items count: {len(merged_result['Items'])}")   # Should be 3 items
    print(f"Address: {merged_result['Address']}")          # Should remain same as first
    
    return merged_result

# Uncomment the line below to test the function
# test_merge_function()  