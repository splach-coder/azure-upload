import re
import copy

def extract_hs_code(text):
    """Extract 9–10 digit HS code from text - allows spaces between digits"""
    if not text:
        return ""

    # Remove all spaces from the text first
    text_no_spaces = text.replace(" ", "")
    
    # Look for 9 or 10 consecutive digits in the cleaned text
    match = re.search(r'\b\d{9,10}\b', text_no_spaces)
    if match:
        return match.group(0)
    
    # Alternative: Look for pattern with optional spaces between digits
    # This matches digits with possible spaces: "9503 001 000" or "9503001000"
    pattern = r'\b(\d[\s]?){8,9}\d\b'
    match = re.search(pattern, text)
    if match:
        # Remove spaces from the matched result
        return match.group(0).replace(" ", "")

    return ""

def merge_invoice_and_pl(inv_result, pl_result):
    merged = copy.deepcopy(inv_result)  # start with invoice structure
    
    inv_items = inv_result.get("Items", [])
    pl_items = pl_result.get("Items", [])
    
    if len(inv_items) != len(pl_items):
        raise ValueError(f"Item length mismatch: Invoice has {len(inv_items)}, PL has {len(pl_items)}")
    
    merged_items = []
    for inv_item, pl_item in zip(inv_items, pl_items):
        # merge dictionaries (invoice first, then PL to avoid overwriting)
        merged_item = {**inv_item, **pl_item}
        merged_items.append(merged_item)
    
    merged["Items"] = merged_items
    
    # merge top-level keys as well
    for key, value in pl_result.items():
        if key != "Items":  # already handled separately
            merged[key] = value
    
    return merged

def fix_hs_codes(invoice_data):
    """
    Fixes HS codes that are shifted down by one position.
    When an item has a missing HS code, all subsequent items have 
    the HS code from the previous item.
    """
    items = invoice_data["Items"]
    
    # Find the index where HS code is missing
    missing_index = -1
    for i, item in enumerate(items):
        hs_code = item.get("HS CODE")
        is_missing = not hs_code or (isinstance(hs_code, dict) and len(hs_code) == 0)
        
        if is_missing:
            missing_index = i
            break
    
    # If no missing HS code found, return as is
    if missing_index == -1:
        return invoice_data
    
    # Shift HS codes: move each HS code from next item to current item
    # Starting from the missing index
    for i in range(missing_index, len(items) - 1):
        items[i]["HS CODE"] = items[i + 1]["HS CODE"]
    
    # The last item will have no HS code after the shift
    # Remove it if it has no valid data (null/0 values)
    last_item = items[-1]
    if (not last_item.get("Amount") and 
        (not last_item.get("Quantity") or last_item.get("Quantity") is None) and 
        last_item.get("Qty") == 0):
        items.pop()  # Remove the last item
    else:
        # If last item has data, just remove its HS code
        if "HS CODE" in last_item:
            del last_item["HS CODE"]
    
    return invoice_data