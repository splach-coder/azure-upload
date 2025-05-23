import logging
from bs4 import BeautifulSoup
import re
import difflib
from collections import defaultdict
from datetime import datetime
import fitz


def extract_text_from_pdf(pdf_path):
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    
    # Extract text from all pages
    text = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text += page.get_text()
        
    return text  

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
    
def normalize_number(value: str) -> str:
    if value is None:
        return ""
    return value.replace(" ", "").replace(".", "").replace(",", ".")

def clean_incoterm(inco : str) -> list :
    if inco is not None:
        return inco.split(' ', maxsplit=1)
    else :
        return ["", ""]

def clean_customs_code(value : str) -> str:
    if value is not None:
        return value.replace(')', '').replace(' ', '')
    else :
        ""

def clean_vat_number(value : str) -> str:
    if value is not None:
        return value.replace('.', '').replace(' ', '')
    else :
        ""

def combine_invoices_by_address(invoices, similarity_threshold=0.8):
    """
    Combines invoices with similar addresses into a single invoice object.

    Args:
        invoices (list): List of invoice dictionaries with 'Inv Ref', 'Adrress', 'Items', and totals.
        similarity_threshold (float): Threshold for determining address similarity (0-1).

    Returns:
        list: Processed list of combined or separate invoices.
    """
    def normalize_address(address):
        """Normalize full address for comparison."""
        address_fields = [
            address[0] ,
            address[1] ,
            address[2] ,
            address[3] ,
            address[4] 
        ]
        return ' '.join(str(field).lower() for field in address_fields if field)
    
    def are_addresses_similar(addr1, addr2, threshold):
        """Determine if two addresses are similar based on a similarity ratio."""
        if len(addr1) > 0 or len(addr2) > 0:
            return True 
        ratio = difflib.SequenceMatcher(None, addr1, addr2).ratio()
        return ratio >= threshold

    # Group invoices by similar addresses
    grouped_invoices = defaultdict(list)
    processed_addresses = []

    for invoice in invoices:
        if len(invoice.get('Address', [])) > 0:  
            address = normalize_address(invoice.get('Address', []))
        else :
            address = []    
        matched_group = None

        # Find a matching group for the current address
        for group_addr in processed_addresses:
            if are_addresses_similar(address, group_addr, 0.8):
                matched_group = group_addr
                break

        # Handle empty address scenario
        if not matched_group and not address:
            # Merge with the first group if exists, else create new
            if processed_addresses:
                matched_group = processed_addresses[0]
            else:
                matched_group = address

        # Add to the matched group or create a new group
        if matched_group:
            grouped_invoices[matched_group].append(invoice)
        else:
            grouped_invoices[address].append(invoice)
            processed_addresses.append(address)

    # Combine grouped invoices
    combined_invoices = []
    for group, group_invoices in grouped_invoices.items():
        if len(group_invoices) == 1:
            # No combination needed
            combined_invoices.append(group_invoices[0])
        else:

            # Combine invoices
            combined_invoice = {
                "Vat Number": group_invoices[0]["Vat Number"],
                "Inv Reference": " + ".join(inv["Inv Reference"] for inv in group_invoices),
                "Inv Date": group_invoices[0]["Inv Date"],
                "Other Ref": group_invoices[0]["Other Ref"],
                "Incoterm": group_invoices[0]["Incoterm"],
                "Currency": group_invoices[0]["Currency"],
                "Customs Code": group_invoices[0]["Customs Code"],
                "Address": group_invoices[0]["Address"],
                "Items": [item for inv in group_invoices for item in inv.get("Items", [])],
                "Gross weight Total": sum(inv.get("Gross weight Total", 0) for inv in group_invoices),
                "Total Net": sum(item.get("Net", 0) for inv in group_invoices for item in inv.get("Items", [])),
                "Total": sum(item.get("Amount", 0) for inv in group_invoices for item in inv.get("Items", [])),
            }

            combined_invoices.append(combined_invoice)

    return combined_invoices

def is_invoice(filename):
    pattern = r"^\d+\.pdf$"
    return re.match(pattern, filename, re.IGNORECASE) is not None

def fill_origin_country_on_items(items: list) -> list:
    origin = ""
    for item in items:
        if item.get("Origin") is not None:
            origin = item.get("Origin")
        else :
            item["Origin"] = origin
            
    return items 

def extract_totals_info(item):

    # Clean HTML content using Beautiful Soup
    soup = BeautifulSoup(item, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)

    # Define regex patterns to extract required values
    exit_office_pattern = r"Kantoor van uitgang is:\s*([A-Z0-9]+)"
    freight_pattern = r"Vrachtkost:\s*([\d.,-]+)\s*EUR|Vrachtkost:\s*([\d.,]+)€"
    colli_pattern = r"Aantal colli:\s*(\d+)"

    # Extract values using regex
    exit_office_match = re.search(exit_office_pattern, text)
    freight_match = re.search(freight_pattern, text)
    colli_match = re.search(colli_pattern, text)

    # Prepare the result dictionary
    result = {
        "Exit office": exit_office_match.group(1) if exit_office_match else None,
        "Freight": freight_match.group(1) if freight_match and freight_match.group(1) else (freight_match.group(2) if freight_match and freight_match.group(2) else None),
        "Collis": colli_match.group(1) if colli_match else None
    }

    return result

def change_date_format(date_str):
    # Convert from dd.mm.yyyy to dd/mm/yyyy
    try:
        date_obj = datetime.strptime(date_str, '%d.%m.%Y')
        return date_obj.strftime('%d/%m/%Y')
    except ValueError:
        return "Invalid date format"

def extract_ref(text):
    # Define regex patterns for the required information
    inv_number_pattern = r'CI\s?\d{7}(?: - \d)?'  # Optional '- d' part

    # Search for the patterns in the text
    inv_number_match = re.search(inv_number_pattern, text)

    # Extract the information if found
    inv_number = inv_number_match.group(0) if inv_number_match else None

    return inv_number

def clean_number(input_value: str) -> str:
    # Use a regular expression to keep only digits, periods, and commas
    cleaned_value = re.sub(r'[^0-9.,]', '', input_value)
    return cleaned_value

def extract_clean_email_body(raw_email: str) -> str:
    """Extracts and cleans the main body text from an HTML email."""
    try:
        soup = BeautifulSoup(raw_email, 'html.parser')

        # Remove unnecessary elements like scripts, styles, and hidden elements
        for tag in soup(['script', 'style', 'head', 'meta', 'link', 'title', '[hidden]']):
            tag.decompose()

        # Extract visible text only
        body_text = soup.get_text(separator='\n', strip=True)

        # Remove excessive whitespace and clean the text
        cleaned_text = '\n'.join(line.strip() for line in body_text.splitlines() if line.strip())

        return cleaned_text

    except Exception as e:
        print(f"Error while extracting email body: {e}")
        return ""    
 