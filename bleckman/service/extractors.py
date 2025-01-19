import fitz
import json

from bleckman.helpers.functions import normalize_number, safe_float_conversion

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

def extract_text_from_first_page_arrs(pdf_path):
    """
    Extracts text from specified coordinates on the first page of a PDF.
    Returns an array with two subarrays: one for 'collis' and another for 'gross'.

    Args:
        pdf_path (str): The path to the PDF file.
        collis_coords (list of tuple): List of coordinates for 'collis'.
        gross_coords (list of tuple): List of coordinates for 'gross'.

    Returns:
        list: Two subarrays, one for 'collis' and another for 'gross'.
    """
    
    # Coordinates for Collis and Gross
    collis_coords = [
        (159, 425, 246, 448),
        (247, 425, 324, 448),
        (325, 425, 411, 448),
        (413, 425, 476, 448),
        (477, 425, 540, 448)
    ]

    gross_coords = [
        (157, 447, 247, 472),
        (248, 447, 324, 472),
        (324, 447, 410, 472),
        (413, 447, 478, 472),
        (477, 447, 540, 472)
    ]
    
    pdf_document = fitz.open(pdf_path)
    extracted_collis = []
    extracted_gross = []

    # Get the first page
    first_page = pdf_document[0]

    # Extract 'collis' data
    for (x0, y0, x1, y1) in collis_coords:
        rect = fitz.Rect(x0, y0, x1, y1)
        text = first_page.get_text("text", clip=rect).strip()
        extracted_collis.append(safe_float_conversion(normalize_number(text)) if text else 0.00)

    # Extract 'gross' data
    for (x0, y0, x1, y1) in gross_coords:
        rect = fitz.Rect(x0, y0, x1, y1)
        text = first_page.get_text("text", clip=rect).strip()
        extracted_gross.append(safe_float_conversion(normalize_number(text))  if text else 0.00)

    pdf_document.close()

    return [extracted_collis, extracted_gross]