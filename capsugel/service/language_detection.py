import fitz  # PyMuPDF
from googletrans import Translator
import logging

def read_pdf(file_path):
    text = ''
    with fitz.open(file_path) as pdf_document:
        page = pdf_document[0]
        text = page.get_text()
            
    return text

def detect_language(file_path):
    text = read_pdf(file_path)
    if not text.strip():
        logging.error("No text found in the PDF.")
        return None
    
    translator = Translator()
    try:
        result = translator.detect(text)
        return result.lang
    except Exception as e:
        return None
