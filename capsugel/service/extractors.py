import logging
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

def extract_structured_data_from_pdf_invoice(pdf_path, keyword_params, fallbacks):
    """
    Extract structured data from a PDF based on specific keywords and relative coordinates.

    Parameters:
        pdf_path (str): Path to the PDF file.
        keyword_params (dict): Keywords and parameters for extraction.
            Format: {keyword: (search_radius, space)}
                - search_radius: (width, height) of the extraction rectangle.
                - space: Horizontal space from the keyword to start the extraction area.
        fallbacks (dict): Fallback keywords and parameters.

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

        for keyword, params in keyword_params.items():
            rects = page.search_for(keyword)
            if rects:
                keyword_occurrences[keyword] = (rects, params)
            elif keyword in fallbacks:
                # Attempt to use fallback keyword
                fallback = list(fallbacks[keyword].items())[0]
                fallback_keyword, fallback_params = fallback
                rects = page.search_for(fallback_keyword)
                if rects:
                    keyword_occurrences[fallback_keyword] = (rects, fallback_params)

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
                results.append(record)

    # Close the PDF file
    doc.close()

    return json.dumps(results, indent=4)

def extract_customs_code_from_pdf_invoice(pdf_path, keyword_params={"Preferential Text:" : ((700, 30), -200)}):
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

def merge_incomplete_records_invoice(extracted_data):
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
    for record in extracted_data:
        # Check if the record is incomplete
        is_record_missing = len(record) < 7

        if is_record_missing:
            if incomplete_record is None:
                # Store the incomplete record for future merging
                incomplete_record = record
            else:
                # Merge with the next incomplete record
                incomplete_record.update(record)

                if(len(incomplete_record) >= 7):
                    merged_results.append(incomplete_record)
                    incomplete_record = None  # Reset for the next potential merge
        else:
            # Add the complete record directly to results
            merged_results.append(record)    

    # Handle any remaining incomplete record if at the end
    if incomplete_record is not None:
        merged_results.append(incomplete_record)

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
    potential_codes_pattern = r'[A-Z]{2}\s?\d{6}'
    
    # Find all matches in the text
    matches = re.findall(potential_codes_pattern, text)
    
    # Filter valid matches using is_valid_code
    for match in matches:
        if is_valid_code(match):
            return match
    
    return ""


def extract_customs_code_from_text(text):
    #regex to find potential codes in the text
    potential_codes_pattern = r'[A-Z]{2}\s?\d{4}'
    
    # Find all matches in the text
    matches = re.findall(potential_codes_pattern, text)
    
    def is_valid_code(code):
        pattern = r'[A-Z]{2}\s?\d{4}'
        
        # Use re.match with the re.IGNORECASE flag
        if re.match(pattern, code, re.IGNORECASE):
            return True
        else:
            return False
        
    
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
