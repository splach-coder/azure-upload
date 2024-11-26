import fitz  # PyMuPDF
from googletrans import Translator

def read_pdf(file_path):
    text = ''
    with fitz.open(file_path) as pdf_document:
        for page in pdf_document:
            text += page.get_text()
    return text

def detect_language(file_path):
    text = read_pdf(file_path)
    translator = Translator()
    result = translator.detect(text)
    return result.lang
