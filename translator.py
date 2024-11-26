import fitz  # PyMuPDF
from googletrans import Translator

def read_pdf(file_path):
    text = ''
    with fitz.open(file_path) as pdf_document:
        for page in pdf_document:
            text += page.get_text()
    return text

def detect_language(text):
    translator = Translator()
    result = translator.detect(text)
    return result.lang

def main(file_path):
    # Read the PDF file
    pdf_text = read_pdf(file_path)
    
    # Detect the language of the text
    source_language = detect_language(pdf_text)
    
    return source_language

def translate_dict_keys(input_dict, target_language='en'):
    translator = Translator()
    translated_dict = {}

    for key, value in input_dict.items():
        # Translate the key
        translated_key = translator.translate(key, dest=target_language).text
        # Store the translated key with the original value
        translated_dict[translated_key] = value

    return translated_dict

# Example usage
if __name__ == "__main__":
    inv_keyword_params = {
        "Country of Origin: ": ((25, 0), 5),
        "Commodity Code of country of dispatch:": ((100, 0), 0),
        "Batches:": ((100, 0), 0),
        "Net Weight:": ((100, 0), 0),
        "Total for the line item": ((150, 10), 350),
        "Total freight related surcharges for the item:": ((150, 0), 300),
        "All in Price": ((120, 0), 150),
        "DN Nbr:": ((40, 0), 5)
    }
    file_path = './file.pdf'  # Replace with your PDF file path
    translated_inv_keyword_params = translate_dict_keys(inv_keyword_params, target_language=main(file_path))
    print(translated_inv_keyword_params)