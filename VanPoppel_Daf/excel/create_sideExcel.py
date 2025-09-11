import json
import logging
from AI_agents.Mistral.MistralDocumentQA import MistralDocumentQA
import fitz  # PyMuPDF
import base64

def extract_clean_excel_from_pdf(base64_pdf: str, filename):
    prompt = """
    Extract the following fields from the provided document in JSON format.
    Pay special attention to the items table - extract ALL numeric values exactly as they appear.
    
    **Required Fields:**
    1. "delivery_address": ["company_name", "street", "city", "postal_code", "country"]
    2. "VAT_NO_delivery": "str"
    3. "EORI_NO_delivery": "str"
    4. "INCOTERM": "str"
    5. "INVOICE_NO": "str"
    6. "invoice_date": "YYYY/MM/DD"
    7. "STAT_NO": "str"
    8. "COUNTRY_OF_ORIGIN": "str" as 2 letter country code
    9. "DESTINATION": "str" as 2 letter country code
    10. "Exporter_Reference_No": "str"
    11. "Currency": "str"
    12. "items": [
        {
          "ORDER_NUMBER": "str",
          "TRANSP_NO": "str", 
          "CHASSIS_NUMBER": "str",
          "TYPE": "str",
          "TYPE_CODE": "str",
          "QTY": number,
          "GROSS_WEIGHT": number,
          "NETT_WEIGHT": number,
          "LOAD_LIST": number,
          "AMOUNT_EUR": number,
          "FREIGHT_CHARGE": "str",
          "TOTAL": number
        }
      ]
    
    **CRITICAL EXTRACTION RULES FOR NUMBERS:**
    - GROSS_WEIGHT, NETT_WEIGHT, TOTAL: Extract exact numeric values from the table
    - Look for weight columns that may contain values like: 1520, 1100, 7600, etc.
    - TOTAL is typically the rightmost column with monetary values
    - If a cell contains "1520" extract it as 1520, not 0
    - If a cell contains "7600" extract it as 7600, not 0
    - QTY is usually 1 for trucks/vehicles
    - NEVER default numeric fields to 0 unless the cell is truly empty
    
    **Table Extraction Tips:**
    - Scan the entire table row by row
    - Look for patterns like: ORDER_NO | TRANSP_NO | CHASSIS | TYPE | QTY | GROSS_WT | NET_WT | AMOUNT | TOTAL
    - Weight values are often 4-digit numbers (1000-9999)
    - Total amounts are usually the last numeric column
    
    **Extraction Rules:**
    - If "company_name" is not explicit, use the most likely company name in address
    - "VAT_NO_delivery" and "EORI_NO_delivery" start with 'GB' if UK
    - "INCOTERM" is usually 3-letter code (e.g., 'FCA')
    - "invoice_date" must be 'YYYY/MM/DD' format
    - "COUNTRY_OF_ORIGIN" and "DESTINATION" as 2-letter ISO codes
    - "Exporter_Reference_No" starts with 'NLREX'
    
    **Output:**
    Return ONLY valid JSON. No explanations or notes.
"""

    # Mistral call
    qa = MistralDocumentQA()
    response = qa.ask_document(base64_pdf, prompt, filename=filename)

    # Clean response
    raw = response.replace("```", "").replace("json", "").strip()
    parsed = json.loads(raw)
    
    return parsed

def get_invoice_page_number(base64_pdf: str, filename):
    prompt = """Find the INVOICE page number in this PDF. 

    INVOICE page has: customer info, accounting data, delivery details, structured business tables, recipient addresses, items with prices
    BARCODE page has: Y-codes (Y4019, Y4026), product codes, "CAB" labels, weight totals

    If NO invoice page exists (only barcode pages), return 0.
    If invoice page exists, return ONLY the page number. Example: 2 or if the pdf has only one page and its the invoice return 1.

    Return ONLY the number, no other text."""

    # Mistral call
    qa = MistralDocumentQA()
    response = qa.ask_document(base64_pdf, prompt, filename=filename)

    # Clean response - convert to integer
    try:
        raw = response.strip()
        invoice_page = int(raw)
        return invoice_page
    except ValueError:
        # If AI returns non-numeric response, assume no invoice
        return 0 

def extract_specific_page_as_base64(base64_pdf: str, page_number: int, rotate_right: bool = False):
    """
    Extract a specific page from PDF and return as base64
    
    Args:
        base64_pdf: Base64 encoded PDF
        page_number: Page number to extract (1-based)
        rotate_right: Whether to rotate the page 90 degrees clockwise
    
    Returns:
        Base64 encoded PDF containing only the specified page
    """
    try:
        # Decode base64 PDF
        pdf_bytes = base64.b64decode(base64_pdf)
        
        # Open PDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Check if page exists
        if page_number < 1 or page_number > doc.page_count:
            raise ValueError(f"Page {page_number} does not exist. PDF has {doc.page_count} pages.")
        
        # Create new PDF with only the specified page
        new_doc = fitz.open()
        
        # Get the specific page (convert to 0-based index)
        page = doc[page_number - 1]
        
        # Rotate if needed
        if rotate_right:
            page.set_rotation(90)  # Rotate 90 degrees clockwise
        
        # Insert page into new document
        new_doc.insert_pdf(doc, from_page=page_number - 1, to_page=page_number - 1)
        
        # Convert to bytes
        pdf_bytes_output = new_doc.tobytes()
        
        # Close documents
        doc.close()
        new_doc.close()
        
        # Convert back to base64
        return base64.b64encode(pdf_bytes_output).decode('utf-8')
        
    except Exception as e:
        logging.error(f"Error extracting page {page_number}: {str(e)}")
        raise      
      