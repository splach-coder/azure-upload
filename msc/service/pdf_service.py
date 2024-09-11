import fitz

def extract_text_from_coordinates(pdf_path, coordinates):
    pdf_document = fitz.open(pdf_path)
    extracted_text = {}

    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        page_text = []

        for (x0, y0, x1, y1) in coordinates:
            rect = fitz.Rect(x0, y0, x1, y1)
            text = page.get_text("text", clip=rect)
            page_text.append(text.strip())

        extracted_text[page_num + 1] = page_text

    return extracted_text
