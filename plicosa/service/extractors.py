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

def extract_text_from_last_page(pdf_path, coordinates, key_map):
    pdf_document = fitz.open(pdf_path)
    extracted_text = []

    # Get the last page
    last_page = pdf_document[-1]  # Index -1 gives the last page

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
