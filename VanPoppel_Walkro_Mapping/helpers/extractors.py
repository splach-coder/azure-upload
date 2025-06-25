import json
import logging
from AI_agents.Mistral.MistralDocumentQA import MistralDocumentQA

def extract_clean_excel_from_pdf(base64_pdf: str, filename):
    
    prompt = """
Extract the following information from the provided PDF document and format it into a JSON structure.
Ensure the following:
- All numerical values must be real numbers (convert numbers like "23,32" to 23.32 if it's using ',' as a decimal separator).
- Dates must follow the format YYYY-MM-DD.
- Countries must be represented by their 2-letter ISO codes.
- Remove any units (e.g., 'kg') or symbols from values.
- Omit any fields that are not present in the document.
- Strictly follow the dictionary structure with no additional text or explanation.

Note:
In the source documents, commas (,) are used as decimal separators. For example, "23,32" means 23.32 — parse accordingly.

Extract only the invoice data and ignore other pages. Extract the following fields:
- net_weight_kg: from the invoice weight in ton (convert to kg)
- invoice_date: from the invoice date
- license_plate: from Kenteken/Pasnr.
- total_amount: from the total amount
- currency: from the currency used
- description: from the description of the commodity
- package: from the package details (Extract from invoice exp 52 PK)
- date: from the invoice date
- transport_fee: from any transport fee if available
- address: [company name, street, city, postal code, country (in 2-letter ISO code)]

Dictionary Structure:
invoice_data = {
    "VAT exporter": "<VAT number without dots or spaces>",
    "Transport fee": "<transport fee if available>",
    "Address": {
        "Company name": "<name of the company>",
        "Street": "<street and number>",
        "Postcode": "<postcode>",
        "City": "<city>",
        "Country": "<country code>"
    },
    "Items": [
        {
            "Description": "<description of the commodity>",
            "Net weight": <gross weight in kg as a number>,
            "Invoice value": <invoice value as a number>,
            "Currency": "<currency code>",
            "Invoice date": "<invoice date in YYYY-MM-DD format>",
            "License plate": "<license plate or pass number>",
            "Package": "<package details>",
            "Date": "<date in YYYY-MM-DD format>"
        }
    ]
}

Instructions:
- VAT Exporter: Extract and normalize the VAT number (no spaces or dots).
- Address: Extract Company name, street, postcode, city, and country (as ISO code).
- Transport fee: Extract transport fee if available
- Items: Extract the commodity data:
  - Description: Commodity description
  - Net weight: Convert weight from ton to kg
  - Invoice value: Extract as a number (if available)
  - Currency: Extract currency code (if available)
  - Invoice date: From invoice date
  - License plate: Kenteken/Pasnr.
  - Package: Package details
  - Date: Invoice date
  
 Ensure that the extracted data strictly adheres to the JSON format provided above. Output only valid JSON. No additional commentary or explanation.
"""
    
    # Mistral call
    qa = MistralDocumentQA()
    response = qa.ask_document(base64_pdf, prompt, filename=filename)

    # Clean response
    raw = response.replace("```", "").replace("json", "").strip()
    
    parsed = json.loads(raw)
    
    return parsed