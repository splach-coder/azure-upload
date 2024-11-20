import os
import re
import fitz
import json

def extract_data_from_pdf(pdf_path, keyword_params):
    # Initialize a list to hold the results
    results = []
    
    # Open the PDF file
    doc = fitz.open(pdf_path)
    
    # Iterate over each page in the PDF
    for page in doc:
        # Get the text of the page for searching
        text = page.get_text("text")
        
        # Initialize a dictionary to hold the extracted information for the current page
        page_data = {}
        
        # Iterate over each keyword and its corresponding parameters
        for keyword, (search_radius, space) in keyword_params.items():
            # Find all occurrences of the keyword
            start_pos = 0
            while True:
                start_pos = text.find(keyword, start_pos)
                if start_pos == -1:
                    break  # No more occurrences found
                
                # Get the rectangle coordinates for the keyword
                keyword_rects = page.search_for(keyword)
                if keyword_rects:
                    x0, y0, x1, y1 = keyword_rects[0]  # Get the first occurrence's rectangle
                    
                    # Define the area next to the keyword to extract the text
                    rect = fitz.Rect(x1 + space, y0, x1 + space + search_radius[0], y1 + search_radius[1])
                    extracted_text = page.get_text("text", clip=rect).strip()
                    
                    # Add the extracted data to the dictionary
                    page_data[keyword] = extracted_text
                    
                # Move to the next occurrence
                start_pos += len(keyword)

        # Only append the page_data if it contains any data
        if page_data:
            results.append(page_data)

    # Close the PDF file
    doc.close()
    
    return json.dumps(results, indent=2)

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

def extract_text_from_last_page(pdf_path, coordinates, page, key_map):
    pdf_document = fitz.open(pdf_path)
    extracted_text = []

    # Get the last page
    last_page = pdf_document[page-1]  # Index -1 gives the last page

    # Extract text from specific coordinates on the last page
    for (x0, y0, x1, y1) in coordinates:
        rect = fitz.Rect(x0, y0, x1, y1)
        text = last_page.get_text("text", clip=rect)
        extracted_text.append(text.strip())

    # Ensure the number of extracted texts matches the key_map
    if len(extracted_text) != len(key_map):
        raise ValueError("Length of extracted text and key map must be equal for the last page.")

    # Map the extracted text to the provided key_map
    data_dict = dict(zip(key_map, extracted_text))

    return json.dumps(data_dict, indent=2)

def extract_structured_data_from_pdf_invoice(pdf_path, keyword_params):
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
    # Initialize a list to hold structured results
    results = []

    # Open the PDF file
    doc = fitz.open(pdf_path)

    # Iterate over each page in the PDF
    for page in doc:
        # Find all occurrences of the keywords on the page
        keyword_occurrences = {}

        for keyword in keyword_params.keys():
            # Find all rectangles matching the keyword
            keyword_occurrences[keyword] = page.search_for(keyword)

        # Keep extracting data while occurrences exist for all keywords
        while True:
            # Initialize a structured object for the current group of keywords
            record = {}
            found_any = False

            for keyword, rects in keyword_occurrences.items():
                if not rects:
                    continue  # No occurrences left for this keyword
                
                found_any = True  # Mark that we found at least one keyword

                # Get the first occurrence's rectangle
                rect = rects.pop(0)
                x0, y0, x1, y1 = rect

                # Get the search parameters for this keyword
                search_radius, space = keyword_params[keyword]

                # Define the area next to the keyword to extract the text
                extract_rect = fitz.Rect(x1 + space, y0, x1 + space + search_radius[0], y1 + search_radius[1])
                extracted_text = page.get_text("text", clip=extract_rect).strip()

                # Add the extracted text to the record under the keyword
                record[keyword] = extracted_text

            # Stop if no keywords were found in this iteration
            if not found_any:
                break

            # Only append the record if it contains data for all specified keywords
            if record:
                results.append(record)

    # Close the PDF file
    doc.close()

    return json.dumps(results, indent=4)

def merge_incomplete_records_invoice(extracted_data, keyword_params):
    """
    Merges incomplete records with the next record that has the missing data.

    Parameters:
        extracted_data (list): The list of extracted JSON data.
        keyword_params (dict): The keyword parameters to check completeness against.
        
    Returns:
        list: The corrected and merged data.
    """

    extracted_data = json.loads(extracted_data)
    # Iterate through the list of extracted records
    merged_results = []
    incomplete_record = None

    # Loop through all extracted records
    for i, record in enumerate(extracted_data):
        # If the record is incomplete, we store it for merging
        if len(record) < len(keyword_params):
            if incomplete_record is None:
                incomplete_record = record
            else:
                # Merge with the next record (incomplete + next complete)
                incomplete_record.update(record)
                merged_results.append(incomplete_record)
                incomplete_record = None
        else:
            # Add a complete record
            merged_results.append(record)

    return merged_results

def is_valid_code(code):
    # Define the regex pattern with case insensitivity
    pattern = r'^[A-Z]{2}\d{6}$'
    
    # Use re.match with the re.IGNORECASE flag
    if re.match(pattern, code, re.IGNORECASE):
        return True
    else:
        return False

def extract_exitoffices_from_body(text):   
    # Regex to find potential codes in the text
    potential_codes_pattern = r'[A-Z]{2}\d{6}'
    
    # Find all matches in the text
    matches = re.findall(potential_codes_pattern, text)
    
    # Filter valid matches using is_valid_code
    for match in matches:
        if is_valid_code(match):
            return match
    
    return ""

def find_page_in_invoice(pdf_path, keywords=["Invoice Total Net", "Total VAT", "Total Value Due", "* Last Page"]):
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
            if any(keyword in page_text for keyword in keywords):
                pages_with_data.append(page_number + 1)  # Page numbers are 1-based
            
        if pages_with_data:
            return pages_with_data
        else:
            return "No relevant data found in this document."

    except Exception as e:
        return f"An error occurred: {str(e)}"
