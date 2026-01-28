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

COUNTRY_MAPPING = {
    "AFGHANISTAN": "AF", "ALAND ISLANDS": "AX", "ALBANIA": "AL", "ALGERIA": "DZ", "AMERICAN SAMOA": "AS",
    "ANDORRA": "AD", "ANGOLA": "AO", "ANGUILLA": "AI", "ANTARCTICA": "AQ", "ANTIGUA AND BARBUDA": "AG",
    "ARGENTINA": "AR", "ARMENIA": "AM", "ARUBA": "AW", "AUSTRALIA": "AU", "AUSTRIA": "AT",
    "AZERBAIJAN": "AZ", "BAHAMAS": "BS", "BAHRAIN": "BH", "BANGLADESH": "BD", "BARBADOS": "BB",
    "BELARUS": "BY", "BELGIUM": "BE", "BELIZE": "BZ", "BENIN": "BJ", "BERMUDA": "BM",
    "BHUTAN": "BT", "BOLIVIA": "BO", "BOSNIA AND HERZEGOVINA": "BA", "BOTSWANA": "BW", "BOUVET ISLAND": "BV",
    "BRAZIL": "BR", "BRITISH INDIAN OCEAN TERRITORY": "IO", "BRUNEI DARUSSALAM": "BN", "BULGARIA": "BG", "BURKINA FASO": "BF",
    "BURUNDI": "BI", "CAMBODIA": "KH", "CAMEROON": "CM", "CANADA": "CA", "CAPE VERDE": "CV",
    "CAYMAN ISLANDS": "KY", "CENTRAL AFRICAN REPUBLIC": "CF", "CHAD": "TD", "CHILE": "CL", "CHINA": "CN",
    "CHRISTMAS ISLAND": "CX", "COCOS (KEELING) ISLANDS": "CC", "COLOMBIA": "CO", "COMOROS": "KM", "CONGO": "CG",
    "CONGO, THE DEMOCRATIC REPUBLIC OF THE": "CD", "COOK ISLANDS": "CK", "COSTA RICA": "CR", "COTE D'IVOIRE": "CI", "CROATIA": "HR",
    "CUBA": "CU", "CYPRUS": "CY", "CZECH REPUBLIC": "CZ", "DENMARK": "DK", "DJIBOUTI": "DJ",
    "DOMINICA": "DM", "DOMINICAN REPUBLIC": "DO", "ECUADOR": "EC", "EGYPT": "EG", "EL SALVADOR": "SV",
    "EQUATORIAL GUINEA": "GQ", "ERITREA": "ER", "ESTONIA": "EE", "ETHIOPIA": "ET", "FALKLAND ISLANDS (MALVINAS)": "FK",
    "FAROE ISLANDS": "FO", "FIJI": "FJ", "FINLAND": "FI", "FRANCE": "FR", "FRENCH GUIANA": "GF",
    "FRENCH POLYNESIA": "PF", "FRENCH SOUTHERN TERRITORIES": "TF", "GABON": "GA", "GAMBIA": "GM", "GEORGIA": "GE",
    "GERMANY": "DE", "GHANA": "GH", "GIBRALTAR": "GI", "GREECE": "GR", "GREENLAND": "GL",
    "GRENADA": "GD", "GUADELOUPE": "GP", "GUAM": "GU", "GUATEMALA": "GT", "GUERNSEY": "GG",
    "GUINEA": "GN", "GUINEA-BISSAU": "GW", "GUYANA": "GY", "HAITI": "HT", "HEARD ISLAND AND MCDONALD ISLANDS": "HM",
    "HOLY SEE (VATICAN CITY STATE)": "VA", "HONDURAS": "HN", "HONG KONG": "HK", "HUNGARY": "HU", "ICELAND": "IS",
    "INDIA": "IN", "INDONESIA": "ID", "IRAN, ISLAMIC REPUBLIC OF": "IR", "IRAQ": "IQ", "IRELAND": "IE",
    "ISLE OF MAN": "IM", "ISRAEL": "IL", "ITALY": "IT", "JAMAICA": "JM", "JAPAN": "JP",
    "JERSEY": "JE", "JORDAN": "JO", "KAZAKHSTAN": "KZ", "KENYA": "KE", "KIRIBATI": "KI",
    "KOREA, DEMOCRATIC PEOPLE'S REPUBLIC OF": "KP", "KOREA, REPUBLIC OF": "KR", "KUWAIT": "KW", "KYRGYZSTAN": "KG", "LAO PEOPLE'S DEMOCRATIC REPUBLIC": "LA",
    "LATVIA": "LV", "LEBANON": "LB", "LESOTHO": "LS", "LIBERIA": "LR", "LIBYAN ARAB JAMAHIRIYA": "LY",
    "LIECHTENSTEIN": "LI", "LITHUANIA": "LT", "LUXEMBOURG": "LU", "MACAO": "MO", "MACEDONIA, THE FORMER YUGOSLAV REPUBLIC OF": "MK",
    "MADAGASCAR": "MG", "MALAWI": "MW", "MALAYSIA": "MY", "MALDIVES": "MV", "MALI": "ML",
    "MALTA": "MT", "MARSHALL ISLANDS": "MH", "MARTINIQUE": "MQ", "MAURITANIA": "MR", "MAURITIUS": "MU",
    "MAYOTTE": "YT", "MEXICO": "MX", "MICRONESIA, FEDERATED STATES OF": "FM", "MOLDOVA, REPUBLIC OF": "MD", "MONACO": "MC",
    "MONGOLIA": "MN", "MONTENEGRO": "ME", "MONTSERRAT": "MS", "MOROCCO": "MA", "MOZAMBIQUE": "MZ",
    "MYANMAR": "MM", "NAMIBIA": "NA", "NAURU": "NR", "NEPAL": "NP", "NETHERLANDS": "NL",
    "NETHERLANDS ANTILLES": "AN", "NEW CALEDONIA": "NC", "NEW ZEALAND": "NZ", "NICARAGUA": "NI", "NIGER": "NE",
    "NIGERIA": "NG", "NIUE": "NU", "NORFOLK ISLAND": "NF", "NORTHERN MARIANA ISLANDS": "MP", "NORWAY": "NO",
    "OMAN": "OM", "PAKISTAN": "PK", "PALAU": "PW", "PALESTINIAN TERRITORY, OCCUPIED": "PS", "PANAMA": "PA",
    "PAPUA NEW GUINEA": "PG", "PARAGUAY": "PY", "PERU": "PE", "PHILIPPINES": "PH", "PITCAIRN": "PN",
    "POLAND": "PL", "PORTUGAL": "PT", "PUERTO RICO": "PR", "QATAR": "QA", "REUNION": "RE",
    "ROMANIA": "RO", "RUSSIAN FEDERATION": "RU", "RWANDA": "RW", "SAINT HELENA": "SH", "SAINT KITTS AND NEVIS": "KN",
    "SAINT LUCIA": "LC", "SAINT PIERRE AND MIQUELON": "PM", "SAINT VINCENT AND THE GRENADINES": "VC", "SAMOA": "WS", "SAN MARINO": "SM",
    "SAO TOME AND PRINCIPE": "ST", "SAUDI ARABIA": "SA", "SENEGAL": "SN", "SERBIA": "RS", "SEYCHELLES": "SC",
    "SIERRA LEONE": "SL", "SINGAPORE": "SG", "SLOVAKIA": "SK", "SLOVENIA": "SI", "SOLOMON ISLANDS": "SB",
    "SOMALIA": "SO", "SOUTH AFRICA": "ZA", "SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS": "GS", "SPAIN": "ES", "SRI LANKA": "LK",
    "SUDAN": "SD", "SURINAME": "SR", "SVALBARD AND JAN MAYEN": "SJ", "SWAZILAND": "SZ", "SWEDEN": "SE",
    "SWITZERLAND": "CH", "SYRIAN ARAB REPUBLIC": "SY", "TAIWAN, PROVINCE OF CHINA": "TW", "TAJIKISTAN": "TJ", "TANZANIA, UNITED REPUBLIC OF": "TZ",
    "THAILAND": "TH", "TIMOR-LESTE": "TL", "TOGO": "TG", "TOKELAU": "TK", "TONGA": "TO",
    "TRINIDAD AND TOBAGO": "TT", "TUNISIA": "TN", "TURKEY": "TR", "TURKMENISTAN": "TM", "TURKS AND CAICOS ISLANDS": "TC",
    "TUVALU": "TV", "UGANDA": "UG", "UKRAINE": "UA", "UNITED ARAB EMIRATES": "AE", "UNITED KINGDOM": "GB",
    "UNITED STATES": "US", "UNITED STATES MINOR OUTLYING ISLANDS": "UM", "URUGUAY": "UY", "UZBEKISTAN": "UZ", "VANUATU": "VU",
    "VENEZUELA": "VE", "VIET NAM": "VN", "VIRGIN ISLANDS, BRITISH": "VG", "VIRGIN ISLANDS, U.S.": "VI", "WALLIS AND FUTUNA": "WF",
    "WESTERN SAHARA": "EH", "YEMEN": "YE", "ZAMBIA": "ZM", "ZIMBABWE": "ZW"
}

def get_iso_country(text):
    if not text:
        return ""
    
    text_upper = str(text).upper().strip()
    
    found_matches = []
    # Find all countries mentioned in the text and their positions
    for name, code in COUNTRY_MAPPING.items():
        match = re.search(r'\b' + re.escape(name) + r'\b', text_upper)
        if match:
            found_matches.append((match.start(), code))
    
    if not found_matches:
        # Fallback: if no match found, just clean and return the original string
        return text_upper
    
    # Sort by the start position in the text (first appearing country wins)
    found_matches.sort(key=lambda x: x[0])
    
    return found_matches[0][1] # Return the ISO code for the first country found

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

def repair_damaged_items(damaged_items, content, doc_type="Invoice"):
    """Specific repair for only damaged items."""
    from AI_agents.OpenAI.custom_call import CustomCall
    import json
    import logging

    if not damaged_items:
        return []

    extractor = CustomCall()
    
    schema = ""
    if doc_type == "Invoice":
        schema = """
{
  "Items": [
    {
      "HS CODE": "string",
      "Quantity": 0,
      "Amount": 0.0,
      "Description": "string"
    }
  ]
}"""
    else:
        schema = """
{
  "Items": [
    {
      "Quantity": 0,
      "Net Weight": 0.0,
      "Gross Weight": 0.0,
      "Ctns": 0,
      "Description": "string"
    }
  ]
}"""

    prompt = f"""
You are an expert data extraction engine specialized in logistics documents ({doc_type}).
I have identified some "damaged" items that are missing critical fields. 
Please find and re-extract ONLY these items from the raw OCR text provided below.

DAMAGED ITEMS (Partial data):
{json.dumps(damaged_items, indent=2)}

CONSTRAINTS:
- Output ONLY a single plain JSON object containing the repaired items.
- Ensure "HS CODE", "Quantity", and "Amount" are present for Invoices.
- Ensure "Net Weight" and "Gross Weight" are present for Packing Lists.
- Return items in the same order as provided in DAMAGED ITEMS.

SCHEMA:
{schema}

TEXT CONTENT:
{content}
"""
    
    try:
        response = extractor.send_request("System", prompt)
        if not response:
            return []
        
        json_str = response.replace("```json", "").replace("```", "").strip()
        data = json.loads(json_str)
        return data.get("Items", [])
    except Exception as e:
        logging.error(f"Damaged Item Repair failed: {e}")
        return []

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
  "Origin Country": "string",
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
  "Origin Country": "string",
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
- For "Origin Country", look for phrases like "FROM [COUNTRY] TO..." and extract the FIRST country mentioned as the origin.
- For Invoices, focus on capturing "HS CODE" (Commodity), "Quantity" (Collis), and "Amount" (Invoice value).
- For Packing Lists, focus on "Net Weight" (NW) and "Gross Weight" (GW) for each item.

SCHEMA:
{schema}

TEXT CONTENT:
{content}
"""
    
    logging.info(f"--- AI REPAIR PROMPT ({doc_type}) ---")
    logging.info(prompt)
    logging.info(f"------------------------------------")
    
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

