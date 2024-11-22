import re
from bs4 import BeautifulSoup
import fitz

def extract_email_data(email_body):
    # Define regex patterns for each required field
    patterns = {
        "Marken_reference": r"Marken reference:\s*(\S+)",
        "Number": r"Number:\s*(\d+)",
        "Weight": r"Weight:\s*(\d+\s*kg)",
        "Location": r"Location:\s*(\S+)",
        "HS_code": r"HS code:\s*(\d+)",
        "EORI": r"EORI:\s*(?:.*?)([A-Z]{2}\d{10})",  # Adjusted pattern for EORI
        "Depart_from": r"Depart from BRU - (\S+)"
    }

    # Initialize a dictionary to store the extracted values
    extracted_data = {}

    # Extract values using regex
    for key, pattern in patterns.items():
        match = re.search(pattern, email_body)
        if match:
            extracted_data[key] = match.group(1)

    return extracted_data

def extract_and_clean(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    data = soup.get_text()
    
    return data

def extract_text_from_coordinates(pdf_path, coordinates, page_number=None):
    """
    Extracts text from a specified list of coordinates in a PDF document.
    
    Parameters:
        pdf_path (str): Path to the PDF file.
        coordinates (list): List of tuples, each containing (x0, y0, x1, y1) coordinates.
        page_number (int, optional): The page number to extract text from. 
                                      If None, extracts from all pages.
    
    Returns:
        list: A list of extracted text from the specified pages.
    """
    pdf_document = fitz.open(pdf_path)

    # If no page number is provided, loop through all pages
    if page_number is None:
        pages_to_process = range(len(pdf_document))  # Process all pages
    else:
        # If page_number is provided, process only that page (1-based index)
        pages_to_process = [page_number - 1]  # Convert to 0-based index

    extracted_text = []

    for page_num in pages_to_process:
        page = pdf_document[page_num]

        page_text = []

        for idx, (x0, y0, x1, y1) in enumerate(coordinates):
            rect = fitz.Rect(x0, y0, x1, y1)
            text = page.get_text("text", clip=rect).strip()
            
            # If there is any text in this block, add it to the results
            if text:
                page_text.append(text)
            else:
                page_text.append("")

        extracted_text.extend(page_text)

    return extracted_text