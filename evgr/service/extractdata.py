import fitz
import json

def extract_text_from_page_2(pdf_path, coordinates, key_map = ["Vissel", "Stay", "Loyds"]):
    pdf_document = fitz.open(pdf_path)
    
    # Ensure the PDF has at least 2 pages
    if len(pdf_document) < 2:
        raise ValueError("The PDF must have at least 2 pages.")
    
    # Select only page 2 (index 1 because pages are 0-based in PyMuPDF)
    page = pdf_document[1]
    page_text = []

    # Extract text from specific coordinates
    for (x0, y0, x1, y1) in coordinates:
        rect = fitz.Rect(x0, y0, x1, y1)
        text = page.get_text("text", clip=rect)
        page_text.append(text.strip())

    # Check if the number of extracted texts matches the number of keys in the key_map
    if len(page_text) != len(key_map):
        raise ValueError("Length of data list and key map must be equal.")

    # Map the extracted text to the provided key_map and return as a JSON object
    data_dict = dict(zip(key_map, page_text))
    return json.dumps(data_dict, indent=2)

def extract_text_from_pages(pdf_path, coordinates, key_map=["BL Number", "Origin Country", "Description", "container", "packages", "article", "Gross Weight"]):
    pdf_document = fitz.open(pdf_path)
    
    # Ensure the PDF has at least 2 pages
    if len(pdf_document) < 2:
        raise ValueError("The PDF must have at least 2 pages.")
    
    all_page_data = []

    # Loop through pages starting from page 2 (index 1 because pages are 0-based)
    for page_num in range(1, len(pdf_document)):
        page = pdf_document[page_num]
        page_text = []

        # Extract text from specific coordinates
        for (x0, y0, x1, y1) in coordinates:
            rect = fitz.Rect(x0, y0, x1, y1)
            text = page.get_text("text", clip=rect)
            page_text.append(text.strip())

        # Check if the number of extracted texts matches the number of keys in the key_map
        if len(page_text) != len(key_map):
            raise ValueError(f"Length of data list and key map must be equal on page {page_num + 1}.")

        # Map the extracted text to the provided key_map and append the result to the list
        data_dict = dict(zip(key_map, page_text))
        all_page_data.append({
            "page": page_num + 1,  # Store the page number (1-based index)
            "data": data_dict
        })

    return json.dumps(all_page_data, indent=2)