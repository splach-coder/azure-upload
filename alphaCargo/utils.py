import re
import copy

def extract_hs_code(text):
    """Extract 9–10 digit HS code from text - allows spaces between digits"""
    if not text:
        return ""

    # Remove all spaces from the text first
    text_no_spaces = text.replace(" ", "")
    
    # Look for 9 or 10 consecutive digits in the cleaned text
    match = re.search(r'\b\d{8,10}\b', text_no_spaces)
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
    
    # If one list is empty, we can't really zip. But let's try to be resilient.
    if not inv_items and not pl_items:
        return merged

    if len(inv_items) != len(pl_items):
        # logging.warning(f"Item length mismatch: Invoice has {len(inv_items)}, PL has {len(pl_items)}")
        # In case of mismatch, we might just take whichever is longer or return what we have
        # For now keep the exception but maybe just return merged if user wants it fluid
        pass
    
    merged_items = []
    # Use the shorter length to avoid Indexing error if we don't raise
    for i in range(min(len(inv_items), len(pl_items))):
        inv_item = inv_items[i]
        pl_item = pl_items[i]
        merged_item = {**pl_item, **inv_item} # Invoice data takes precedence
        merged_items.append(merged_item)
    
    # If invoice has more items, add them
    if len(inv_items) > len(pl_items):
        merged_items.extend(inv_items[len(pl_items):])
    
    merged["Items"] = merged_items
    
    # merge top-level keys as well
    for key, value in pl_result.items():
        if key != "Items" and value:  # already handled separately
            if not merged.get(key): # Only overwrite if missing in invoice
                merged[key] = value
    
    return merged

def fix_hs_codes(invoice_data):
    """
    Fixes HS codes that are shifted down by one position.
    When an item has a missing HS code, all subsequent items have 
    the HS code from the previous item.
    """
    if not invoice_data or "Items" not in invoice_data:
        return invoice_data

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
    amount = last_item.get("Amount")
    qty = last_item.get("Quantity") or last_item.get("Qty")
    
    if (not amount or amount == 0) and (not qty or qty == 0):
        items.pop()  # Remove the last item
    else:
        # If last item has data, just remove its HS code
        if "HS CODE" in last_item:
            del last_item["HS CODE"]
    
    return invoice_data

def detect_missing_fields(data, doc_type="Invoice"):
    """Determines if the extracted data is missing critical fields or has incomplete items."""
    missing = []
    
    items = data.get("Items", [])
    if not items or len(items) == 0:
        missing.append("Items")
    else:
        # Check for item-level completeness
        if doc_type == "Invoice":
            missing_hs_count = sum(1 for item in items if not item.get("HS CODE") and not item.get("Commodity"))
            missing_qty_count = sum(1 for item in items if not item.get("Quantity") and not item.get("Qty"))
            missing_amount_count = sum(1 for item in items if not item.get("Amount") and not item.get("Invoice value"))
            
            if len(items) > 0:
                if (missing_hs_count / len(items)) > 0.1:
                    missing.append("HS CODE")
                if (missing_qty_count / len(items)) > 0.1:
                    missing.append("Quantity")
                if (missing_amount_count / len(items)) > 0.1:
                    missing.append("Amount")
        else: # Packing List
            missing_nw_count = sum(1 for item in items if not item.get("Net Weight") and not item.get("Net"))
            missing_gw_count = sum(1 for item in items if not item.get("Gross Weight") and not item.get("Gross"))
            
            if len(items) > 0:
                if (missing_nw_count / len(items)) > 0.1:
                    missing.append("Net Weight")
                if (missing_gw_count / len(items)) > 0.1:
                    missing.append("Gross Weight")

    if doc_type == "Invoice":
        if not data.get("Invoice Number"): missing.append("Invoice Number")
        if not data.get("Inco Term"): missing.append("Inco Term")
        if not data.get("Total Value"): missing.append("Total Value")
    else: # Packing List
        if not data.get("Total Gross"): missing.append("Total Gross")
        if not data.get("Total Net"): missing.append("Total Net")

    return missing

def repair_with_ai(content, doc_type="Invoice", existing_data=None):
    """Uses LLM to extract data from raw OCR content when DI fails or is incomplete."""
    from AI_agents.OpenAI.custom_call import CustomCall
    import json
    import logging

    extractor = CustomCall()
    
    schema = ""
    if doc_type == "Invoice":
        schema = """
{
  "Invoice Number": "string",
  "Inco Term": "string",
  "Total Value": 0.0,
  "Currency": "string",
  "Items": [
    {
      "HS CODE": "string",
      "Quantity": 0,
      "Amount": 0.0
    }
  ]
}"""
    else:
        schema = """
{
  "Total Gross": 0.0,
  "Total Net": 0.0,
  "Total Packages": 0,
  "Items": [
    {
      "Quantity": 0,
      "Net Weight": 0.0,
      "Gross Weight": 0.0,
      "Ctns": 0
    }
  ]
}"""

    prompt = f"""
You are an expert data extraction engine specialized in logistics documents ({doc_type}).
Extract the following information from the raw OCR text provided below into a single valid JSON object.

CONSTRAINTS:
- Output ONLY a single plain JSON object. No markdown, no extra text.
- Numbers must be numeric (no commas in JSON, use dot for decimal).
- Extract ALL items from the item table.
- For Invoices, focus on capturing "HS CODE" (Commodity), "Quantity" (Collis), and "Amount" (Invoice value).
- For Packing Lists, focus on "Net Weight" (NW) and "Gross Weight" (GW) for each item.

SCHEMA:
{schema}

TEXT CONTENT:
{content}
"""
    
    try:
        response = extractor.send_request("System", prompt)
        if not response:
            return None
        
        json_str = response.replace("```json", "").replace("```", "").strip()
        data = json.loads(json_str)
        return data
    except Exception as e:
        logging.error(f"AI Repair failed: {e}")
        return None

