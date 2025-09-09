import logging
from bs4 import BeautifulSoup
import json
from AI_agents.Mistral.MistralDocumentQA import MistralDocumentQA

def extract_email_body(html_content):
    """
    Extracts the visible body text from an Outlook HTML email.
    
    Args:
        html_content (str): The raw HTML content of the email.
    
    Returns:
        str: Cleaned plain-text body of the email.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Optionally: remove script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()

    # Find the <body> tag content if it exists
    body = soup.find("body")
    text = body.get_text(separator="\n") if body else soup.get_text(separator="\n")

    # Clean extra spaces and lines
    clean_text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())

    return clean_text

def extract_clean_excel_from_pdf(base64_pdf: str, filename):
    prompt = """
    Extract all invoice items from the provided document(s) and return the results in strict JSON format as specified below.
JSON Structure Requirements:
 Copy{
  "Items": [
    {
      "InvoiceNumber": "string",
      "InvoiceDate": "dd-mm-yyyy",
      "Description": "string",
      "HSCode": "string",
      "Origin": "string (if available, else empty)",
      "NetWeight": number,
      "Quantity": number,
      "UnitPrice": number,  // Use the value labeled as "Price" or "Net Price" (if provided). If not, leave as 0 or empty.
      "Amount": number,    // **ALWAYS the LAST numeric value in the row** (regardless of column headers).
      "Currency": "string"
    }
  ]
}

Extraction Rules:


No Omissions:

Extract every line item from all pages of the invoice.
Do not stop after a fixed number of rows.
If the invoice spans multiple pages, combine all items into a single JSON array.



Data Formatting:

Dates: Always use dd-mm-yyyy format.
Numbers:

Use dots (.) for decimals (e.g., 374.00).
Remove thousands separators (e.g., 10,000 → 10000).
Ensure NetWeight, Quantity, UnitPrice, and Amount are numeric.


Currency: Always include the 3-letter currency code (e.g., GBP, USD).
Empty Fields: If a field (e.g., Origin) is missing, use an empty string "".



Column Mapping:

Description: Use the item description (e.g., MFX Rivet Stainl Steel DH 4.8x30).
HSCode: Use the commodity code (e.g., 8308200090).
NetWeight: Extract the individual item weight (e.g., 12.4).

If only the total weight is provided, distribute it proportionally by quantity.


UnitPrice: Use the value labeled as "Price" (if provided). If no price is listed, leave as 0 or empty.
Amount: ALWAYS the LAST numeric value in the row (regardless of column headers).

Example: If the row ends with 81.74, that is the Amount.

Validation:

Do not calculate or derive values.
Do not cross-check Quantity × UnitPrice = Amount.
If the document is unclear, flag ambiguous fields with empty string like "" and request clarification.

Output:

Return only valid JSON—no explanations, notes, or placeholders.
If the document is unclear, flag ambiguous fields with empty string like "".

Example Output:
 Copy{
  "Items": [
    {
      "InvoiceNumber": "101118820",
      "InvoiceDate": "09-09-2025",
      "Description": "MFX Rivet Stainl Steel DH 4.8x30",
      "HSCode": "8308200090",
      "Origin": "CN",
      "NetWeight": 12.4,
      "Quantity": 2000,
      "UnitPrice": 40.87,
      "Amount": 81.74,
      "Currency": "GBP"
    },
    {
      "InvoiceNumber": "101118820",
      "InvoiceDate": "09-09-2025",
      "Description": "PLIA Al/steel DH 3.2x10",
      "HSCode": "8308200090",
      "Origin": "CN",
      "NetWeight": 19.26,
      "Quantity": 18000,
      "UnitPrice": 3.62,
      "Amount": 65.16,
      "Currency": "GBP"
    }
  ]
}

Key Clarifications:

Amount is always the last numeric value in the row.
UnitPrice is only the value labeled as "Price" or "Net Price" (if provided).
No calculations—use only what is explicitly stated in the document.
    """

    # Mistral call
    qa = MistralDocumentQA()
    response = qa.ask_document(base64_pdf, prompt, filename=filename)

    # Clean response
    raw = response.replace("```", "").replace("json", "").strip()
    parsed = json.loads(raw)
    
    return parsed