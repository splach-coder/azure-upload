import logging
from bs4 import BeautifulSoup
import fitz
import json
import re

from TennecoMonroe.helpers.functions import is_valid_number

def extract_text_from_first_page(pdf_path, coordinates, key_map, page=[1]):
    pdf_document = fitz.open(pdf_path)
    extracted_text = []

    # Get the first page
    first_page = pdf_document[page[0] - 1]#minus one to make 0 indexed

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

def find_page_in_invoice(pdf_path, keywords=["Packaging", "No.units", "Weight (KG)", "Terms of delivery", "Total w/o VAT"]):
    try:
        # Open the PDF file
        pdf_document = fitz.open(pdf_path)
        
        # Ensure the PDF has at least 1 page
        if len(pdf_document) < 1:
            return "The PDF is empty or has no pages."

        # Search for pages containing all the keywords
        pages_with_data = []
        for page_number in range(len(pdf_document)):
            page = pdf_document[page_number]
            page_text = page.get_text("text")

            # Check if all keywords are found on this page
            if all(keyword in page_text for keyword in keywords):
                pages_with_data.append(page_number + 1)  # Page numbers are 1-based
            
        if pages_with_data:
            return pages_with_data
        else:
            return "No relevant data found in this document."

    except Exception as e:
        return f"An error occurred: {str(e)}"

def extract_dynamic_text_from_pdf(pdf_path, x_coords, y_range, key_map, page, row_height=9, gap=1.1):
    pdf_document = fitz.open(pdf_path)
    extracted_text = []
    
    # Get the first page
    first_page = pdf_document[page[0] - 1]  # Assuming we are always extracting from the first page

    # Initialize y_start and y_end based on the y_range
    y_start, y_end = y_range

    # Loop through the y-coordinates, extracting rows of text
    current_y = y_start
    stopLoop = False 
    while True:
        if stopLoop:
            break
            
        row_data = []
        for x in x_coords:
            rect = fitz.Rect(x[0], current_y, x[1], current_y + row_height)
            text = first_page.get_text("text", clip=rect).strip()
            row_data.append(text)     

        # Check if the row meets the criteria
        if (
            len(row_data[0]) > 4 and
            is_valid_number(row_data[0]) and  # First element must be a number
            len(row_data) >= 4 and     # Must have at least 5 elements
            all(is_valid_number(val) for val in row_data[2:])
            ):  # Last three must be numbers
            
            # Map the extracted text to the provided key_map (if the lengths match)
            if len(row_data) != len(key_map):
                raise ValueError("Length of extracted text and key map must be equal.")

            data_dict = dict(zip(key_map, row_data))
            
            extracted_text.append(data_dict)
            current_y += row_height + gap # Move to the next row with a space of 3
        else:
            stopLoop = True 

    return json.dumps(extracted_text, indent=2)

def find_customs_authorisation_coords(pdf_path, page_number):
    pdf_document = fitz.open(pdf_path)
    page = pdf_document[page_number[0] - 1]  # Page numbers are 1-based

    # Search for the text "Customs authorisation No" on the page
    text_instances = page.search_for("Customs authorisation No")

    # If the text is found, get its coordinates
    if text_instances:
        text_rect = text_instances[0]
        x0 = text_rect.x0
        y0 = text_rect.y0
        x1 = text_rect.x1 + 100
        y1 = text_rect.y1

        # Get the whole text in the updated rectangle
        rect = fitz.Rect(x0, y0, x1, y1)
        text = page.get_text("text", clip=rect)

        # Use regex to find the word that matches two characters, maybe space, maybe not, and two numbers
        import re
        match = re.search(r'\b([A-Z]{2}\s?\d{2})\b', text)
        if match:
            return match.group(0)
        else:
            return None
    else:
        return ""
    
def extract_freight_and_exit_office_from_html(html):
    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Extract the body tag content specifically
    body_content = soup.find('body')
    if not body_content:
        return {"error": "Body not found"}

    # Get text from the email body
    body_text = body_content.get_text(separator=' ').strip()

    # Regex for freight (only the number)
    freight_pattern = r"(\d+(?:[.,]\d+)?)\s?€"
    freight_pattern2 = r"(\d+(?:[.,]\d+)?)\s?EUR"
    
    # Regex for exit office (2 letters followed by 6 digits)
    exit_office_pattern = r"\b[A-Z]{2}\d{6}\b"
    
    # Regex for container (4 letters followed by 7 digits)
    container_pattern = r"\b\s*[A-Z]{4}\s*\d{7}\s*\b"
    
    # Search for freight
    freight_match = re.search(freight_pattern, body_text)
    freight = float(freight_match.group(1).replace(',', '.')) if freight_match else None

    # Search for freight
    freight_match2 = re.search(freight_pattern2, body_text)
    freight2 = float(freight_match2.group(1).replace(',', '.')) if freight_match2 else None
    
    # Search for exit office
    exit_office_match = re.search(exit_office_pattern, body_text)
    exit_office = exit_office_match.group(0) if exit_office_match else None
    
    # Search for exit office
    container_match = re.search(container_pattern, body_text)
    container = container_match.group(0) if container_match else ""
    
    logging.error(container)

    return {
        "freight": freight if freight else freight2,
        "exit_office": exit_office,
        "Container": container.replace(" ", "")
    }