import base64
import logging

from bs4 import BeautifulSoup
import fitz
from datetime import datetime

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
    - 'To' address as array: [company name, street, city, postal code, country (change the country name to 2 letter code abbreviation instead of full name)] #if anything is missing, leave it empty string
    - "Bales/Pallets/bags" : ..., #number of bales, pallets or bags
    - "Total Weight in Kgs: (name it GrossWeight)" : ..., #total weight in Kgs as number
    - "Terms of delivery:" , [incoterm, place] #terms of delivery
    - "Country of Origin:" : "...", #country of origin 2 letter code abbreviation
    - "Total amount:" : ..., #total amount as number (note that . is a seperator like 3.960,000 should be 3960.00) 
    - "Currency:" : "..." #currency of the total amount
    - "EORI Number": ..., #EORI number of the company

    Return only a JSON object like:
    {{
        "HSCode": "...",
        "ToAddress": {{
            "company name": CVB Recycling,
            "street": Radiatorenstraat 51,
            "city": Vilvoorde,
            "postal code: 1800,
            "country": BE #change the country name to 2 letter code abbreviation instead of full name
        }}, #if anything is missing, leave it empty string
        "Bales/Pallets/bags" : ..., #number of bales, pallets or bags
        "Terms of delivery": , [incoterm, place] #terms of delivery
        "Country of Origin": : "...", #country of origin 2 letter code abbreviation
        "Total amount": : ..., #total amount as number (note that . is a seperator like 3.960,000 should be 3960.00) 
        "Currency": : ..., #currency of the total amount,
        "GrossWeight": ..., #total weight in Kgs as number,
        "EORI Number": ..., #EORI number of the company
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
    - Transport Costs:

    Return as clean JSON.
    
    note number should be numbers format (pay attention), strings in a string format.

    Here the Email to extract the data from:
    '''{email_body}'''
    """
    call = CustomCall()
    return call.send_request(role="user", prompt_text=prompt)


def detect_sender_flow(email_text: str) -> str:
    if "@coolsolutions.be" in email_text:
        return "coolsolutions"
    elif "@williamsrecycling.co.uk" in email_text:
        return "williamsrecycling"
    else:
        return ""
    
def extract_email_body(html_content: str) -> str:
    """Extracts and cleans the main body text from an HTML email."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove unnecessary elements like scripts, styles, and hidden elements
        for tag in soup(['script', 'style', 'head', 'meta', 'link', 'title', '[hidden]']):
            tag.decompose()
        # Extract visible text only
        body_text = soup.get_text(separator='\n', strip=True)
        # Remove excessive whitespace and clean the text
        cleaned_text = '\n'.join(line.strip() for line in body_text.splitlines() if line.strip())
        return cleaned_text
    except Exception as e:
        print(f"Error while extracting email body: {e}")
        return ""
    
    


def build_items(data):
    item_template = data.get("CargoDetails", {}).get("Items", [])[0]
    
    # Build the new item object
    new_item = {
        "ItemNumber": item_template.get("ItemNumber"),
        "NoOfPackages": item_template.get("NoOfPackages"),
        "PackageCode": item_template.get("PackageCode"),
        "GrossWeightKG": item_template.get("GrossWeightKG"),
        "Description": item_template.get("Description"),
        "HSCode": item_template.get("HSCode"),
        "Total amount": data.get("Total amount"),
        "Currency": data.get("Currency"),
        "ConveyanceRef": data.get("TransportDetails").get("ConveyanceRef"),
        "ArticleNumber": data.get("CargoDetails", {}).get("ArticleNumber"),
        "LloydsNr": data.get("TransportDetails", {}).get("LloydsNr"),
        "Agent": data.get("TransportDetails", {}).get("Agent"),
        "InvoiceRef": data.get("InvoiceRef"),
        "BL": data.get("CargoDetails").get('UCR'),
        "CountryOfOrigin": data.get("Country of Origin"),
        "Date": datetime.now().strftime("%Y-%m-%d")
    }
    
    # Add 'items' array to the data
    data["items"] = [new_item]
    
    return data
       