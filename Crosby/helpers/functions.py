from bs4 import BeautifulSoup
import re
import difflib
from collections import defaultdict

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
    return value.replace(" ", "").replace(".", "").replace(",", ".")  

def clean_incoterm(inco : str) -> list :
    return inco.split(' ', maxsplit=1)

def clean_customs_code(value : str) -> str:
    return value.replace(')', '').replace(' ', '')

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
            address[0]['Company name'],
            address[0]['Street'],
            address[0]['City'],
            address[0]['Postal code'],
            address[0]['Country']
        ]
        return ' '.join(str(field).lower() for field in address_fields if field)
    
    def are_addresses_similar(addr1, addr2, threshold):
        """Determine if two addresses are similar based on a similarity ratio."""
        ratio = difflib.SequenceMatcher(None, addr1, addr2).ratio()
        return ratio >= threshold

    # Group invoices by similar addresses
    grouped_invoices = defaultdict(list)
    processed_addresses = []

    for invoice in invoices:
        address = normalize_address(invoice.get('Adrress'))
        matched_group = None

        # Find a matching group for the current address
        for group_addr in processed_addresses:
            if are_addresses_similar(address, group_addr, similarity_threshold):
                matched_group = group_addr
                break

        # Add to matched group or create a new group
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
                "Inv Ref": " + ".join(inv["Inv Ref"] for inv in group_invoices),
                "Inv Date": group_invoices[0]["Inv Date"],
                "Other Ref": group_invoices[0]["Other Ref"],
                "Incoterm": group_invoices[0]["Incoterm"],
                "Currency": group_invoices[0]["Currency"],
                "Customs Code": group_invoices[0]["Customs Code"],
                "Adrress": group_invoices[0]["Adrress"],
                "Items": [item for inv in group_invoices for item in inv.get("Items", [])],
                "Totals": {
                    "Total Qty": sum(item.get("Qty", 0) for inv in group_invoices for item in inv.get("Items", [])),
                    "Total Gross": sum(item.get("Gross", 0) for inv in group_invoices for item in inv.get("Items", [])),
                    "Total Net": sum(item.get("Net", 0) for inv in group_invoices for item in inv.get("Items", [])),
                    "Total Amount": sum(item.get("Amount", 0) for inv in group_invoices for item in inv.get("Items", [])),
                }
            }
            combined_invoices.append(combined_invoice)

    return combined_invoices

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

def extract_reference(text):
    # Define the regex pattern to find the reference after "ref"
    pattern = r"ref\s+(\w+\s+\w+/\d+)"
    
    # Search for the pattern in the text
    match = re.search(pattern, text)
    
    # Return the matched reference or None if not found
    return match.group(1) if match else None

def clean_numbers(input_string):
    # Use regex to find all digits and join them together
    cleaned_number = ''.join(re.findall(r'\d+', input_string))
    return cleaned_number