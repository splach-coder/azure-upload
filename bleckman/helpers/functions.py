from datetime import datetime
import logging
import fitz
import re
from typing import Any, List, Dict, Tuple, Union
from global_db.countries.functions import get_abbreviation_by_country

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
    
def normalize_number(value: str) -> str:
    return value.replace(" ", "").replace(".", "").replace(",", ".")    

def merge_inputs(dicts):
    """
    Merge a list of dictionaries by combining their keys and keeping the first non-None value for each key.

    Args:
        dicts (list): A list of dictionaries to merge.

    Returns:
        dict: A merged dictionary with non-None values.
    """
    merged_dict = {}

    # Loop through each dictionary
    for d in dicts:
        for key, value in d.items():
            # If the key doesn't exist or the current value is None, update it
            if key not in merged_dict or merged_dict[key] is None:
                merged_dict[key] = value

    return [merged_dict]


def process_invoice_data(input_data: Dict[str, Union[str, List]]) -> Dict[str, Union[str, List]]:
    # Initialize variables for merging
    merged_reference = ""
    merged_total_pallets = 0
    merged_total = 0.0
    merged_items = []
    merged_invoices = []
    merged_totals = []

    # Extract general fields from the first data item
    first_data_item = input_data['data'][0]
    vat_number = first_data_item.get('Vat Number', "")
    inv_date = first_data_item.get('Inv Date', "")
    address = first_data_item.get('Address', [])
    incoterm = first_data_item.get('Incoterm', "")
    
    if len(address) > 1:
        address = merge_inputs(address)
    
    #handle the adress 
    if address[0]["Country"] is not None:
        address[0]["Country"] = get_abbreviation_by_country(address[0].get("Country", ""))
    
    # Remove special characters from Incoterm and split
    cleaned_incoterm = re.sub(r'[+,.]', '', incoterm).split(' ', maxsplit=1)

    # Process and merge all data items
    for item in input_data['data']:
        # Merge references
        if merged_reference:
            merged_reference += f" + {item['Inv Reference']}"
        else:
            merged_reference = item['Inv Reference']

        # Append to invoices array
        merged_invoices.append(item['Inv Reference'])


        if item.get('Total') is not None:
            merged_totals.append(safe_float_conversion(item.get('Total', 0).replace(",", "").replace("\u20ac", "").replace("?", "").replace("$", "").replace("USD", "")))
        else:
            merged_totals.append(0.0)

        # Sum total pallets
        merged_total_pallets += safe_int_conversion(item.get('Total Pallets', 0))
        
        if item.get('Total') is not None:
            # Sum total amount
            merged_total += safe_float_conversion(item.get('Total', 0).replace(",", "").replace("\u20ac", "").replace("?", "").replace("$", "").replace("USD", ""))

        # Process items
        for item_data in item.get('Items', []):
            hs_code = item_data.get('HS code') if item_data.get('HS code') else ''
            cleaned_hs_code = re.sub(r"[^\w]", "", hs_code.strip())
            price_without_currency = ""
            if item_data.get("Price", ""):
                price_without_currency = re.sub(r"[^\d.]", "", item_data.get("Price", ""))
            if item_data.get("Origin", "") is not None:
                if item_data.get("Origin", "") == "TURKIYE":
                    Origin = "TURKEY"
                else:    
                    Origin = item_data.get("Origin", "")#get_abbreviation_by_country(item_data.get("Origin", ""))
            else :
                Origin = ""
            item_entry = {
                "HS code": cleaned_hs_code,
                "Origin": Origin,
                "Pieces": safe_int_conversion(item_data.get("Pieces", 0)),
                "Price": safe_float_conversion(price_without_currency)
            }
            merged_items.append(item_entry)

    # Add currency and instructions based on invoice type
    invoice_type = input_data.get('invoice_type', "").lower()
    currency_symbol = ""
    instruction_1 = ""
    if invoice_type == "euro":
        currency_symbol = "€"
        instruction_1 = "Anine Bing V2 €"
    elif invoice_type == "dollar":
        currency_symbol = "$"
        instruction_1 = "Anine Bing V2 $"

    # Construct the final output JSON
    output_data = {
        "Exit office": input_data.get("Exit office", ""),
        "Reference": input_data.get("Reference", ""),
        "inv Reference": merged_reference,
        "Vat Number": vat_number,
        "Inv Date": inv_date,
        "Address": address,
        "Incoterm": cleaned_incoterm,
        "Total Pallets": merged_total_pallets,
        "Total": merged_total,
        "Items": merged_items,
        "Currency": currency_symbol,
        "Instruction 1": instruction_1,
        "Invoices": merged_invoices,
        "Totals": merged_totals,
        "grosses": input_data.get("grosses", ""),
        "collis": input_data.get("collis", ""),
    }

    return output_data

# Function to test
def process_arrays(collis: List[float], gross: List[float]) -> Tuple[List[float], List[float]]:
    collis = [value for value in collis if value]
    gross = [value for value in gross if value]

    if (len(collis) != len(gross)) or (len(collis) == 0) or (len(gross) == 0):
        return 0.00, 0.00
            
    if len(collis) <= 4:
        collis = collis[-1]
        gross = gross[-1]
    elif len(collis) >= 5:
        if sum(collis[:4]) == collis[-1] :
            collis = collis[-1]
            gross = gross[-1] 
        else :
            collis = sum(collis)
            gross = sum(gross)
                      
    return collis, gross
   