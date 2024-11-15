import json
import fitz
import re
from bs4 import BeautifulSoup

""" i added this function to clean the collis when i extract data from the cmr """

def remove_spaces_from_numeric_strings(s):
    """
    Removes spaces from strings that represent numeric values.
    
    Args:
        s (str): Input string.
        
    Returns:
        str: String with spaces removed if it is numeric.
    """
    # Check if removing spaces gives a numeric string
    return re.sub(r'[^0-9]', '', s)

def extract_text_from_coordinates(pdf_path, coordinates, page_number=None):
    """
    Extracts text from a specified list of coordinates in a PDF document.
    
    Parameters:
        pdf_path (str): Path to the PDF file.
        coordinates (list): List of tuples, each containing (x0, y0, x1, y1) coordinates.
        page_number (int, optional): The page number to extract text from. 
                                      If None, extracts from all pages.
    
    Returns:
        str: A JSON string containing the extracted text from the specified pages.
    """
    pdf_document = fitz.open(pdf_path)

    # If no page number is provided, loop through all pages
    if page_number is None:
        pages_to_process = range(len(pdf_document))  # Process all pages
    else:
        # If page_number is provided, process only that page (1-based index)
        pages_to_process = [page_number - 1]  # Convert to 0-based index

    for page_num in pages_to_process:
        page = pdf_document[page_num]
        page_text = []

        for idx, (x0, y0, x1, y1) in enumerate(coordinates):
            rect = fitz.Rect(x0, y0, x1, y1)
            text = page.get_text("text", clip=rect).strip()
            
            # If there is any text in this block, add it to the results
            if text:
                page_text.append(text)

    return page_text

def extract_table_data_with_dynamic_coordinates(pdf_path):
    """
    Extracts table from the first page of a PDF document based on dynamic coordinates.
    
    Parameters:
        pdf_path (str): Path to the PDF file.
    
    Returns:
        str: A JSON string containing the extracted text from the first page.
    """
    y0, y1 = (442, 453)  # Initial Y coordinates for the first row
    x_coords = [(22, 111), (330, 374), (425, 479)]  # X coordinates for columns
    gap = 34  # Vertical gap to move to the next row

    pdf_document = fitz.open(pdf_path)
    page = pdf_document.load_page(0)  # Only process the first page
    page_text = []

    while True:
        row_text = []
        for x0, x1 in x_coords:
            rect = fitz.Rect(x0, y0, x1, y1)  # Create a rectangle for the column
            text = page.get_text("text", clip=rect).strip()

            # If there is text in the column, add it to the row
            if text:
                row_text.append(text)
        
        # If no text is found for a row, break the loop
        if not row_text or len(row_text) < 3:
            break
        
        page_text.append(row_text)  # Add the row to the page's text data
        y0, y1 = y0 + gap, y1 + gap  # Move to the next row

    return page_text  # Return the data as a JSON string

def handle_body_request(body):
    return extract_and_clean(body)

def extract_and_clean(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    data = soup.get_text()

    # Clean excessive whitespace and newlines
    cleaned_data = re.sub(r'\s+', ' ', data).strip()
    
    # Use regex patterns to isolate each key piece of information
    result = {}
    principal_match = re.search(r'Principal:\s*(.*?)\s*(UK|BE)', cleaned_data)
    reference_match = re.search(r'Reference:\s*(\d+)', cleaned_data)
    exit_port_match = re.search(r'Exit Port BE:\s*(.*?)\s*Freight', cleaned_data)
    # Capture only numbers immediately after "Freight cost:"
    freight_cost_match = re.search(r'Freight cost:\s*(\d+)\s*(\d+)', cleaned_data)

    # Populate result dictionary if matches are found
    if principal_match:
        result['Principal'] = f"{principal_match.group(1).strip()} {principal_match.group(2).strip()}"
    if reference_match:
        result['Reference'] = reference_match.group(1).strip()
    if exit_port_match:
        result['Exit Port BE'] = exit_port_match.group(1).strip()
    if freight_cost_match:
        # Combine both matched numbers if there are two parts, separated by a space
        result['Freight cost'] = f"{freight_cost_match.group(1)}{freight_cost_match.group(2)}"

    parking_trailer_pattern_exact = r"Parking trailer:\s*(\w+)"
    parking_trailer_pattern_fallback = r"[Pp]arking.*?(\w+)"

    exit_port_value = exit_port_match.group(1).strip() if exit_port_match else None

    # Check if Exit Port BE is "Zeebrugge" and extract parking trailer information
    if exit_port_value and exit_port_value.lower() == "zeebrugge":
        # First try to match the exact "Parking trailer:" pattern
        parking_trailer = re.search(parking_trailer_pattern_exact, cleaned_data)

        if parking_trailer:
            result["Parking trailer"] = parking_trailer.group(1)
        else:
            # If not found, use fallback pattern to find any mention of 'parking'
            parking_trailer_fallback = re.search(parking_trailer_pattern_fallback, cleaned_data)
            if parking_trailer_fallback:
                result["Parking trailer"] = parking_trailer_fallback.group(1)    
    
    return result

def extract_cmr_collis_data_with_dynamic_coordinates(pdf_path, page_number):
    """
    Extracts table from the first page of a PDF document based on dynamic coordinates.
    
    Parameters:
        pdf_path (str): Path to the PDF file.
    
    Returns:
        str: A JSON string containing the extracted text from the first page.
    """
    y0, y1 = (273, 286)  # Initial Y coordinates for the first row
    x_coords = [(38, 84), (555, 575)]  # X coordinates for columns
    gap = 20  # Vertical gap to move to the next row

    pdf_document = fitz.open(pdf_path)
    page = pdf_document.load_page(page_number - 1)  #  process the  page
    page_text = []

    while True:
        row_text = []
        for x0, x1 in x_coords:
            rect = fitz.Rect(x0, y0, x1, y1)  # Create a rectangle for the column
            text = page.get_text("text", clip=rect).strip()

            # If there is text in the column, add it to the row
            if text:
                row_text.append(remove_spaces_from_numeric_strings(text))
        
        # If no text is found for a row, break the loop
        if not row_text or len(row_text) <= 1:
            break
        
        json_obj = json.dumps({
            "material_code": row_text[0],
            "Collis": int(row_text[1])
        })
        
        page_text.append(json_obj)  # Add the row to the page's text data
        y0, y1 = y0 + gap, y1 + gap  # Move to the next row

    return page_text  # Return the data as a JSON string

