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
    return value.replace(')', '').replace(' ', '')

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