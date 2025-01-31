import logging
import re
from bs4 import BeautifulSoup

def join_items(data):
    
    # Create a dictionary to store the joined items
    joined_items = {}

    # Iterate over the 'items_collis' list
    for item_collis in data.get('items_collis'):
        # Use the 'Product Code' as the key
        product_code = item_collis.get('Product Code')
        # Initialize the joined item with the 'Collis' value
        joined_items[product_code] = {'Collis': item_collis['Collis']}

    # Iterate over the 'items' list
    for item in data['items']:
        # Use the 'Product Code' as the key
        product_code = item.get('Product Code')
        # Update the joined item with the values from the 'items' list
        if product_code in joined_items:
            joined_items[product_code].update(item)
        else:
            # If the product code is not found, add it to the joined items
            joined_items[product_code] = item

    # Convert the joined items dictionary back to a list
    joined_items_list = list(joined_items.values())

    # Update the original data with the joined items
    data['items'] = joined_items_list
    # Remove the 'items_collis' key
    del data['items_collis']

    return data

def join_invoices(invs):
    if not invs:
        return {}

    # Start with the first invoice as the base
    combined_invoice = invs[0].copy()

    # Iterate through all invoices
    for inv in invs[1:]:
        # Combine 'Inv Reference' and 'Other Ref'
        combined_invoice['Inv Reference'] += '+' + inv['Inv Reference']
        combined_invoice['Other Ref'] += '+' + inv['Other Ref']
        
        # Extend the 'Items' list with items from the current invoice
        combined_invoice['Items'].extend(inv['Items'])

    return combined_invoice

def join_cmrs(cmrs):
    if not cmrs:
        return {}

    # Start with the first invoice as the base
    combined_invoice = cmrs[0].copy()

    # Iterate through all invoices
    for inv in cmrs[1:]:
        # Combine 'Inv Reference' and 'Other Ref'
        combined_invoice['Gross weight total'] += inv['Gross weight total']
        combined_invoice['Net weight total'] += inv['Net weight total']
        combined_invoice['Pallets'] += inv['Pallets']
        
        # Extend the 'Items' list with items from the current invoice
        combined_invoice['items'].extend(inv['items'])

    return combined_invoice

def join_cmr_invoice_objects(inv, cmr):
    # Create a dictionary to store the joined items, starting with invoice items
    joined_items = {}

    # First add all invoice items - these are our source of truth
    for item in inv['Items']:
        product_code = item.get('Material Code', "")
        joined_items[product_code] = item.copy()

    # Then selectively update with CMR data where product codes match
    for cmr_item in cmr['items']:
        cmr_product_code = cmr_item.get('Product Code', "")
        if cmr_product_code in joined_items:
            # Only copy specific fields from CMR that we want to update
            inv_item = joined_items[cmr_product_code]
            # Add CMR-specific fields while preserving invoice data
            if 'Gross Weight' in cmr_item:
                inv_item['Gross Weight'] = cmr_item['Gross Weight']
            if 'Pieces' in cmr_item:
                inv_item['Pieces'] = cmr_item['Pieces']
            if 'HS code' in cmr_item:
                inv_item['HS code'] = cmr_item['HS code']
            if 'Collis' in cmr_item:
                inv_item['Collis'] = cmr_item['Collis']
            # Add any other CMR fields that should update invoice data here

    # Convert the joined items dictionary back to a list
    joined_items_list = list(joined_items.values())

    # Create the final combined object, prioritizing invoice data
    combined_object = {
        'Inv Reference': inv['Inv Reference'],
        'Inv Date': inv['Inv Date'],
        'Other Ref': inv['Other Ref'],
        'Vat Number': inv['Vat Number'],
        'Incoterm': inv['Incoterm'],
        'Total': inv['Total'],
        'Currency': inv['Currency'],
        'Customs code': inv['Customs code'],
        'Wagon': inv['Wagon'],
        'Address': inv['Address'],
        'Items': joined_items_list,
        'Gross weight total': cmr['Gross weight total'],
        'Net weight total': cmr['Net weight total'],
        'Pallets': cmr['Pallets']
    }

    return combined_object

def handle_body_request(body):
    return extract_and_clean(body)

def extract_and_clean(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    data = soup.get_text()

    # Clean excessive whitespace and newlines
    cleaned_data = re.sub(r'\s+', ' ', data).strip()
    
    # Use regex patterns to isolate each key piece of information
    result = {}
    principal_match = re.search(r'Principal:\s*(.*?)\s*(UK|BE)', cleaned_data)
    reference_match = re.search(r'Reference:\s*(\d+)', cleaned_data)
    exit_port_match = re.search(r'Exit Port BE:\s*(.*?)\s*Freight', cleaned_data)
    # Capture only numbers immediately after "Freight cost:"
    freight_cost_match = re.search(r'Freight cost:\s*(\d+)\s*(\d+)', cleaned_data)

    # Populate result dictionary if matches are found
    if principal_match:
        result['Principal'] = f"{principal_match.group(1).strip()} {principal_match.group(2).strip()}"
    if reference_match:
        result['Reference'] = reference_match.group(1).strip()
    if exit_port_match:
        result['Exit Port BE'] = exit_port_match.group(1).strip()
    if freight_cost_match:
        # Combine both matched numbers if there are two parts, separated by a space
        result['Freight cost'] = f"{freight_cost_match.group(1)}{freight_cost_match.group(2)}"

    parking_trailer_pattern_exact = r"Parking trailer:\s*(\w+)"
    parking_trailer_pattern_fallback = r"[Pp]arking.*?(\w+)"

    exit_port_value = exit_port_match.group(1).strip() if exit_port_match else None

    # Check if Exit Port BE is "Zeebrugge" and extract parking trailer information
    if exit_port_value and exit_port_value.lower() == "zeebrugge":
        # First try to match the exact "Parking trailer:" pattern
        parking_trailer = re.search(parking_trailer_pattern_exact, cleaned_data)

        if parking_trailer:
            result["Parking trailer"] = parking_trailer.group(1)
        else:
            # If not found, use fallback pattern to find any mention of 'parking'
            parking_trailer_fallback = re.search(parking_trailer_pattern_fallback, cleaned_data)
            if parking_trailer_fallback:
                result["Parking trailer"] = parking_trailer_fallback.group(1)    
    
    return result

