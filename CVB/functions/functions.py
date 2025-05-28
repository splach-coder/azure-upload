import base64
import logging

import fitz

from AI_agents.OpenAI.custom_call import CustomCall


def extract_text_from_pdf(base64_file):
    try:
        pdf_bytes = base64.b64decode(base64_file)
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            text = "\n".join([page.get_text() for page in doc])
        return text
    except Exception as e:
        logging.error(f"Failed to extract PDF: {e}")
        return ""

def extract_info_from_proforma(text):
    prompt = f"""
    Extract the following fields from this proforma invoice:
    - HS code
    - 'To' address as array: [company name, street, city, postal code, country code (2-letter)]
    - "Bales/Pallets/bags" : ..., #number of bales, pallets or bags
    - "Terms of delivery:" , [incoterm, place] #terms of delivery
    - "Country of Origin:" : "...", #country of origin 2 letter code abbreviation
    - "Total amount:" : ..., #total amount as number

    Return only a JSON object like:
    {{
        "HSCode": "...",
        "ToAddress": ["company", "street", "city", "postal code", "country"],
        "Bales/Pallets/bags" : ..., #number of bales, pallets or bags
        "Terms of delivery:" , [incoterm, place] #terms of delivery
        "Country of Origin:" : "...", #country of origin 2 letter code abbreviation
        "Total amount:" : ..., #total amount as number
    }}
    
    Invoice content:
    '''{text}'''
    """
    call = CustomCall()
    return call.send_request(role="user", prompt_text=prompt)

def extract_info_from_email(email_body):
    
    prompt = f"""
    Extract the following fields from the email text below:
    - InvoiceRef
    - Trailer
    - TransportDetails (M/S, LloydsNr, Flag, ETS, ETA, Agent, ConveyanceRef, POL, POD, LoCode, LoCodeNCTS)
    - BookingDetails (DateTimeOfIssue, YRef, UnitNr, ORef, KLMEMO)
    - CargoDetails (UCR, ArticleNumber, ReleaseNote, Items: list of (ItemNumber, NoOfPackages, PackageCode, GrossWeightKG, Description, HSCode))
    - TransportCosts (UK, Belgium)

    Return as clean JSON.

    Email:
    '''{email_body}'''
    """
    call = CustomCall()
    return call.send_request(role="user", prompt_text=prompt)
