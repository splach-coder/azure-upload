from datetime import datetime
import copy
import xml.etree.ElementTree as ET
import requests

def merge_json_items(json_obj):
    """
    Merges invoice_items and packinglist_items arrays into a single 'items' array
    based on matching QUANTITY-SET values.
    
    Args:
        json_obj (dict): JSON object containing invoice_items and packinglist_items
        
    Returns:
        dict: Modified JSON object with merged items array
    """
    # Create a copy to avoid modifying the original
    result = json_obj.copy()
    
    # Initialize empty items array
    result['items'] = []
    
    # Get the arrays
    invoice_items = json_obj.get('invoice_items', [])
    packinglist_items = json_obj.get('packinglist_items', [])
    
    # Check if lengths are equal
    if len(invoice_items) != len(packinglist_items):
        raise ValueError(f"Array lengths don't match: invoice_items({len(invoice_items)}) != packinglist_items({len(packinglist_items)})")
    
    # Create dictionaries for quick lookup by QUANTITY-SET
    invoice_dict = {item.get('QUANTITY-SET'): item for item in invoice_items}
    packinglist_dict = {item.get('QUANTITY-SET'): item for item in packinglist_items}
    
    # Merge items based on QUANTITY-SET
    for quantity_set in invoice_dict.keys():
        if quantity_set in packinglist_dict:
            # Merge the two objects
            merged_item = {}
            merged_item.update(invoice_dict[quantity_set])
            merged_item.update(packinglist_dict[quantity_set])
            result['items'].append(merged_item)
        else:
            raise ValueError(f"QUANTITY-SET '{quantity_set}' not found in packinglist_items")
    
    # Remove the original arrays
    if 'invoice_items' in result:
        del result['invoice_items']
    if 'packinglist_items' in result:
        del result['packinglist_items']
    
    return result

def fetch_exchange_rate(currency_code):
    # Get the current year and month in "YYYYMM" format
    current_date = datetime.now().strftime("%Y%m")

    # Insert the dynamic part into the URL
    url = f"https://www.belastingdienst.nl/data/douane_wisselkoersen/wks.douane.wisselkoersen.dd{current_date}.xml"
    
    # Fetch XML content from the URL
    response = requests.get(url)
    
    if response.status_code == 200:
        # Parse XML content
        root = ET.fromstring(response.content)
        
        # Find the currency block that matches the currency code
        for rate in root.findall("douaneMaandwisselkoers"):
            code = rate.find("muntCode").text
            if code == currency_code:
                foreign_rate = rate.find("tariefInVreemdeValuta").text
                return foreign_rate
    
    return 0.0  # Return None if the currency was not found or request failed

def find_shipping_fee_from_sheet(sheet, value):
    """
    Alternative function that works with an already opened sheet object.
    
    Args:
        sheet: xlrd sheet object
        
    Returns:
        The value from column F if "Shipping Fee:" is found, None otherwise
    """
    # Search through column A (index 0)
    for row in range(sheet.nrows):
        cell_value = sheet.cell_value(row, 0)  # Column A
        
        # Check if the cell contains "Shipping Fee:"
        if isinstance(cell_value, str) and value in cell_value:
            # Get the corresponding value from column F (index 5)
            shipping_fee_value = sheet.cell_value(row, 5)  # Column F
            return shipping_fee_value
    
    # Return None if "Shipping Fee:" was not found
    return None