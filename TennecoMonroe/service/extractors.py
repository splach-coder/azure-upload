import logging
import fitz
import json

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

def extract_dynamic_text_from_pdf(pdf_path, x_coords, y_range, key_map, page, row_height=9, gap=1.5):
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
            return (x0, y0, x1, y1), match.group(0)
        else:
            return (x0, y0, x1, y1), None
    else:
        return ""

