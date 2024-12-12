import logging
from bs4 import BeautifulSoup
import re
import fitz
import json

from ferminich.helpers.functions import remove_non_numeric_chars, safe_float_conversion

def extract_information(text):
    # Define regex patterns for the required information
    inv_number_pattern = r'CI \d{7}(?: - \d)?'  # Optional '- d' part
    location_pattern = r'Locatie goederen:\s*([A-Z]{2})'
    pattern = re.compile(r"(\d+)?\s*(?:colis|colli)\s*(\d+)?\s*–\s*([\d, .]+)?\s*KG")
    
    match = pattern.search(text)
    collis = int(match.group(1)) if match and match.group(1) else 0
    kg = float(match.group(3).replace(",", "").replace(" ", "")) if match and match.group(3) else 0.0
    results = {'colis': collis, 'weight': kg}

    # Search for the patterns in the text
    inv_number_match = re.search(inv_number_pattern, text)
    location_match = re.search(location_pattern, text)

    # Extract the information if found
    inv_number = inv_number_match.group(0) if inv_number_match else None
    location = location_match.group(1) if location_match else None

    return {
        'reference': inv_number,
        **results,
        'location': location
    }
    
def extract_and_clean(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    data = soup.get_text()
    
    return data

def extract_text_from_first_page(pdf_path, coordinates, key_map):
    pdf_document = fitz.open(pdf_path)
    extracted_text = []

    # Get the first page
    first_page = pdf_document[0]

    # Extract text from specific coordinates on the first page
    for (x0, y0, x1, y1) in coordinates:
        rect = fitz.Rect(x0, y0, x1, y1)
        text = first_page.get_text("text", clip=rect)
        extracted_text.append(text.strip())

    # Ensure the number of extracted texts matches the key_map
    if len(extracted_text) != len(key_map):
        raise ValueError("Length of extracted text and key map must be equal for the first page.")

    # Map the extracted text to the provided key_map
    data_dict = dict(zip(key_map, extracted_text))

    return json.dumps(data_dict, indent=2)

def vat_validation(vat_number):
    pattern = re.compile(r'^[A-Z]{2}\s?\d{9,10}$')
    if pattern.match(vat_number):
        return vat_number
    return ""

def extract_vat_number(text):
    """
    Extracts a VAT number from the given text.
    
    Args:
        text (str): The input text to search for a VAT number.
        
    Returns:
        str: The extracted VAT number if found, otherwise an empty string.
    """
    # Define the VAT number pattern
    pattern = r'\b[A-Z]{2}\s?\d{9,10}+\b'
    
    # Search for the VAT number in the text
    match = re.search(pattern, text)
    
    # Return the found VAT number or an empty string
    return match.group(0) if match else ""

def extract_cleaned_invoice_text(pdf_path):
    """
    Filters pages containing 'Invoice & Packing List' and specific fields, then extracts the cleaned text.

    Args:
        pdf_path (str): Path to the input PDF file.

    Returns:
        dict: A dictionary where keys are page numbers (starting from 1) and values are the cleaned page text.
    """
    relevant_pages_text = {}

    with fitz.open(pdf_path) as pdf:
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            text = page.get_text("text")  # Extract full text from the page
            
            # Check if the page contains "Invoice & Packing List" and the specific table fields
            if ("Invoice No" in text and "STANDARD CONDITIONS OF SALES" not in text):
                relevant_pages_text[page_num + 1] = text  # Store text with 1-based page number

    return relevant_pages_text

def extract_invoice_details(data: dict) -> dict:
    """
    Extracts the text between specified headers and returns it as a string.
    
    Parameters:
        data (dict): A dictionary where keys are numbers and values are strings.
        
    Returns:
        str: Extracted text between specified headers.
    """
    extracted_text = {}

    for key, value in data.items():
        # Define the headers to extract text between
        start_header = "Product Code\nDescription\nQuantity\nShipped\nUoM\nNet\nWeight\nUnit Price\nAmount"
        end_header = "Taxable Amount\nVAT Rate\nVAT Amount\nCurrency\nTotal Including VAT"

        # Extract the text between the headers
        try:
            start_index = value.index(start_header) + len(start_header)

            # Attempt to find the end header
            end_index = value.index(end_header)
            extracted_text[key] = value[start_index:end_index].strip()
        except ValueError:
            # If the end header is not found, extract until the end of the value
            if start_header in value:
                start_index = value.index(start_header) + len(start_header)
                extracted_text[key] = value[start_index:].strip()
            else:
                continue

# Now extracted_text will contain the extracted values for each key

    # Return the extracted text
    return extracted_text

def split_items_into_array(text: dict) -> list:
    """
    Splits a string into an array of items based on the condition that each item ends
    with a line containing the word 'Shipping'.

    Parameters:
        text (str): The input text to be split.

    Returns:
        list: An array of items as strings.
    """
    # Initialize variables
    items = []
    
    for key, value in text.items():
        # Split the input text into lines
        lines = value.split("\n")

        current_item = []

        # Iterate through each line
        for line in lines:
            # Add the line to the current item
            current_item.append(line)

            # Check if the current line contains "Shipping"
            if "Shipping" in line:
                # Join the lines of the current item and add to items
                items.append("\n".join(current_item))
                # Reset the current item for the next batch
                current_item = []

        # Handle any remaining lines that weren't added to an item
        if current_item:
            items.append("\n".join(current_item))

    return items

def extract_fields_from_item_text(items: list) -> list:
    """
    Extracts fields from a list of item texts and returns a list of objects with specific fields.

    Parameters:
        items (list): A list of strings where each string contains the text of an item.

    Returns:
        list: A list of dictionaries containing extracted fields.
    """
    extracted_items = []

    for item in items:
        lines = item.split("\n")  # Split the item text into lines
        item_data = {
            "product code": None,
            "Description": None,
            "Quantity": None,
            "Net": None,
            "Total Line Amount": None,
            "Country of Origin": None,
            "Batch": None,
            "Order Number": None,
            "Delivery Number": None,
            "Customs Tariff Code": None,
        }

        # Extract the Product Code (always the first line)
        item_data["product code"] = lines[0].strip()

        # Extract Description (from the second line to the line containing Quantity)
        for i, line in enumerate(lines[1:], start=1):
            if line.replace(".", "").isdigit():  # Look for the Quantity
                if safe_float_conversion(line.strip()) < 9999:
                    item_data["Description"] = " ".join(lines[1:i]).strip()
                    item_data["Quantity"] = safe_float_conversion(line.strip())
                    break

        # Extract Net Weight (line containing 'KG')
        for line in lines:
            if " KG" in line:
                item_data["Net"] = safe_float_conversion(remove_non_numeric_chars(line.strip()))
                break

        # Extract Total Line Amount
        for line in lines:
            if "TOTAL LINE AMOUNT:".lower() in line.lower():
                item_data["Total Line Amount"] = safe_float_conversion(lines[lines.index(line) + 1].strip().replace(",", ""))
                break

        # Extract Country of Origin
        for line in lines:
            if "Country of Origin:" in line:
                item_data["Country of Origin"] = line.split(":")[-1].strip()
                break

        # Extract Batch
        for line in lines:
            if "Batch:" in line:
                item_data["Batch"] = line.split(":")[-1].strip().split()[0]  # Only take the batch number
                break

        # Extract Order Number
        for line in lines:
            if "Order Number:" in line:
                item_data["Order Number"] = line.split(":")[-1].strip()
                break

        # Extract Delivery Number
        for line in lines:
            if "Delivery Number:" in line:
                item_data["Delivery Number"] = line.split(":")[-1].strip()
                break

        # Extract Customs Tariff Code
        for line in lines:
            if "Customs Tariff Code:" in line:
                item_data["Customs Tariff Code"] = line.split(":")[-1].strip()
                break

        extracted_items.append(item_data)

    return extracted_items

def extract_optional_from_pdf_invoice(pdf_path, keyword_params):
    """
    Extract structured data from a PDF based on specific keywords and relative coordinates.

    Parameters:
        pdf_path (str): Path to the PDF file.
        keyword_params (dict): Keywords and parameters for extraction.
            Format: {keyword: (search_radius, space)}
                - search_radius: (width, height) of the extraction rectangle.
                - space: Horizontal space from the keyword to start the extraction area.

    Returns:
        str: JSON-formatted string containing structured extracted data.
    """

    # Open the PDF file
    doc = fitz.open(pdf_path)

    # Iterate over each page in the PDF
    for page in doc:
        # Find all occurrences of the keywords on the page
        keyword_occurrences = {}

        for keyword, params in keyword_params.items():
            rects = page.search_for(keyword)
            if rects:
                keyword_occurrences[keyword] = (rects, params)

        # Extract data for all found keywords
        while any(keyword_occurrences.values()):  # While there are rects to process
            record = {}
            for keyword, (rects, params) in list(keyword_occurrences.items()):
                if not rects:
                    continue  # No more rects for this keyword

                # Process the first rectangle for this keyword
                rect = rects.pop(0)  # Remove the first rectangle
                x0, y0, x1, y1 = rect
                search_radius, space = params

                # Define extraction rectangle relative to the keyword's position
                extract_rect = fitz.Rect(
                    x1 + space, y0, x1 + space + search_radius[0], y1 + search_radius[1]
                )
                extracted_text = page.get_text("text", clip=extract_rect).strip()
                record[keyword] = extracted_text

                # Remove keyword if no more rectangles exist
                if not rects:
                    del keyword_occurrences[keyword]

            # Append record only if it contains data
            if record:
                return record
    # Close the PDF file
    doc.close()

    return {}

def extract_customs_code_from_text(text_obj, text="The exporter of the product"):
    # Extract the text value from the dictionary
    text_value = text_obj.get(text, '')
    
    # Use regex to find text inside parentheses
    matches = re.findall(r'\((.*?)\)', text_value)
    
    string_to_remove = ['Exporter Reference No', 'customs au thorization No.', 'customs authorization No.']
    
    if matches:
        matches = matches[0].lower().replace(string_to_remove[0].lower(), '')
        matches = matches.lower().replace(string_to_remove[1].lower(), '')
        matches = matches.lower().replace(string_to_remove[2].lower(), '')
    
        # Return the matches found
        return matches.upper().replace(" ", "")
    else:
        return ""
    
def clean_array_from_unwanted_items(arr):
    for item in arr:
        if 'Correspondence to:' in item:
            arr.remove(item)
            
    return arr            