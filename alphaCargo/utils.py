import re
import copy

def extract_hs_code(text):
    """Extract 9–10 digit HS code from text - strictly digits, no spaces or special characters"""
    if not text:
        return {}

    # Look for 9 or 10 consecutive digits anywhere in the text
    match = re.search(r'\b\d{9,10}\b', text)
    if match:
        return match.group(0)

    return {}


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

