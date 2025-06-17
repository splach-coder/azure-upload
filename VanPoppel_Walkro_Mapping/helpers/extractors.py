import json
import logging
from AI_agents.Mistral.MistralDocumentQA import MistralDocumentQA

def extract_clean_excel_from_pdf(base64_pdf: str, filename):
    prompt = (
    """
    Extract the following information from the provided PDF document and format it into a JSON structure. 
    Ensure the following:
    - All numerical values must be real numbers (convert numbers like "15.940" to 15940 if it's using '.' as a thousands separator).
    - Dates must follow the format YYYY-MM-DD.
    - Countries must be represented by their 2-letter ISO codes.
    - Remove any units (e.g., 'kg') or symbols from values.
    - Omit any fields that are not present in the document.
    - Strictly follow the JSON structure with no additional text or explanation.

    Note:
    In the source documents, dots (.) are used as **thousands separators**, not decimals. For example:
    "15.940 kg" means 15940 kg — parse accordingly.

    You will find all required fields in the PDF as shown in the sample image.
    Extract the following fields:        
    - hs_code → comes from the Product code        
    - gross_weight_kg → from Weging 2        
    - net_weight_kg → from Netto        
    - origin_country → 2-letter ISO code from the customer address        
    - invoice_number → from Order nr.        
    - invoice_date → from the weighing date        
    - article_number → from Bon nr.  
    - license_plate → from Kenteken/Pasnr.

    JSON Structure:
    {
      "VAT exporter": "<VAT number without dots or spaces>",
      "Commercial reference": "<commercial reference number>",
      "Other ref": "<other reference number>",
      "Name": "<name of the company>",
      "Street + number": "<street and number>",
      "Postcode": "<postcode>",
      "City": "<city>",
      "Country": "<country code>",
      "Items": [
        {
          "Commodity": "<HS code as a number>",
          "Description": "<description of the commodity>",
          "Article": "<article number>",
          "Gross": <gross weight as a number>,
          "Net": <net weight as a number>,
          "Origin": "<origin of goods - 2-letter country code>",
          "Invoice value": <invoice value as a number>,
          "Currency": "<currency code>",
          "Invoice number": "<invoice number>",
          "Invoice date": "<invoice date in YYYY-MM-DD format>",
          "License plate": "<license plate or pass number>"
        }
      ]
    }

    Instructions:
    - VAT Exporter: Extract and normalize the VAT number (no spaces or dots).
    - Reference Numbers: Extract Commercial and Other Reference numbers.
    - Address: Extract name, street, postcode, city, and country (as ISO code).
    - Items: Extract the commodity data:
        • Commodity = Product code (used as HS code)
        • Description = Commodity description
        • Article = Bon nr.
        • Gross = Weging 2 (convert using thousands separator logic)
        • Net = Netto (convert using thousands separator logic)
        • Origin = Derived from customer address (ISO code)
        • Invoice value = Extract as a number (if available)
        • Currency = Extract currency code (if available)
        • Invoice number = Order nr.
        • Invoice date = From weighing date
        • License plate = Kenteken/Pasnr.

    Ensure that the extracted data strictly adheres to the JSON format provided above. Output only valid JSON. No additional commentary or explanation.
    """
)

    # Mistral call
    qa = MistralDocumentQA()
    response = qa.ask_document(base64_pdf, prompt, filename=filename)

    # Clean response
    raw = response.replace("```", "").replace("json", "").strip()
    
    logging.error(raw)
    parsed = json.loads(raw)
    
    return parsed