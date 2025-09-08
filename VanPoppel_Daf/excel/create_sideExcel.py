import json
from AI_agents.Mistral.MistralDocumentQA import MistralDocumentQA

def extract_clean_excel_from_pdf(base64_pdf: str, filename):
    prompt = """
        Extract the following fields from the provided document in JSON format.
Ensure all fields are present, even if empty. Do not add or remove any fields.

**Required Fields:**
1. \"delivery_address\": [\"company_name\", \"street\", \"city\", \"postal_code\", \"country\"]
2. \"VAT_NO_delivery\": \"str\"
3. \"EORI_NO_delivery\": \"str\"
4. \"INCOTERM\": \"str\"
5. \"INVOICE_NO\": \"str\"
6. \"invoice_date\": \"YYYY/MM/DD\"
7. \"STAT_NO\": \"str\"
8. \"COUNTRY_OF_ORIGIN\": \"str\" as 2 letter country code
9. \"DESTINATION\": \"str\" as 2 letter country code
10. \"Exporter_Reference_No\": \"str\"
12. \"Currency\": \"str\"
13. \"items\": [
    {
      \"ORDER_NUMBER\": \"str\",
      \"TRANSP_NO\": \"str\",
      \"CHASSIS_NUMBER\": \"str\",
      \"TYPE\": \"str\",
      \"TYPE_CODE\": \"str\",
      \"QTY\": int,
      \"GROSS_WEIGHT\": int,
      \"NETT_WEIGHT\": int,
      \"LOAD_LIST\": int,
      \"AMOUNT_EUR\": float,
      \"FREIGHT_CHARGE\": \"str\",
      \"TOTAL\": float (the total amount for the line item) - (make sure to extarct as number, not string)
    }
  ]

**Extraction Rules:**
- If \"company_name\" is not explicitly stated, use the most likely company name mentioned in the address block.
- \"VAT_NO_delivery\" and \"EORI_NO_delivery\" must start with 'GB' if the country is the UK.
- \"INCOTERM\" is usually a 3-letter code (e.g., 'FCA').
- \"INVOICE_NO\" is a numeric or alphanumeric code.
- \"invoice_date\" must be in 'YYYY/MM/DD' format.
- \"STAT_NO\" is a numeric code, often labeled as 'STAT. NO.' or similar.
- \"COUNTRY_OF_ORIGIN\" and \"DESTINATION\" are country names should be as the 2 lettres ISO format.
- \"Exporter_Reference_No\" is a code always starting with 'NLREX'.
- \"Currency\" the invoice currency that you can find on the items table.
- \"items\" is an array of objects, one per row in the item table.
- \"TOTAL\" in \"items\" always on the last column on the table make sure u extract it well this is the most important one.
- all Countries must be in 2 letter ISO format.

**Output:**
Return only a valid JSON object. Do not include explanations, notes, or placeholders.
"
}
 Copy{
  "function": {
    "name": "extract_invoice_data",
    "description": "Extracts structured invoice data from a PDF or text document.",
    "parameters": {
      "type": "object",
      "properties": {
        "delivery_address": {
          "type": "array",
          "items": {"type": "string"},
          "description": "[company_name, street, city, postal_code, country as 2 letrres iso code] "
        },
        "VAT_NO_delivery": {"type": "string"},
        "EORI_NO_delivery": {"type": "string"},
        "INCOTERM": {"type": "string"},
        "INVOICE_NO": {"type": "string"},
        "invoice_date": {"type": "string", "format": "date"},
        "STAT_NO": {"type": "string"},
        "COUNTRY_OF_ORIGIN": {"type": "string"},
        "DESTINATION": {"type": "string"},
        "Exporter_Reference_No": {"type": "string"},
        "Currency": {"type": "string"},
        "items": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "ORDER_NUMBER": {"type": "string"},
              "TRANSP_NO": {"type": "string"},
              "CHASSIS_NUMBER": {"type": "string"},
              "TYPE": {"type": "string"},
              "TYPE_CODE": {"type": "string"},
              "QTY": {"type": "integer"},
              "GROSS_WEIGHT": {"type": "integer"},
              "NETT_WEIGHT": {"type": "integer"},
              "LOAD_LIST": {"type": "integer"},
              "AMOUNT_EUR": {"type": "number"},
              "FREIGHT_CHARGE": {"type": "string"},
              "TOTAL": {"type": "number"} (the total amount for the line item its the last column)
            },
            "required": [
              "ORDER_NUMBER", "TRANSP_NO", "CHASSIS_NUMBER", "TYPE", "TYPE_CODE",
              "QTY", "GROSS_WEIGHT", "NETT_WEIGHT", "LOAD_LIST", "AMOUNT_EUR",
              "FREIGHT_CHARGE", "TOTAL"
            ]
          }
        }
      },
      "required": [
        "delivery_address", "VAT_NO_delivery", "EORI_NO_delivery", "INCOTERM",
        "INVOICE_NO", "invoice_date", "STAT_NO", "COUNTRY_OF_ORIGIN",
        "DESTINATION", "Exporter_Reference_No", "items", "Currency"
      ]
    }
  }
}
    """

    # Mistral call
    qa = MistralDocumentQA()
    response = qa.ask_document(base64_pdf, prompt, filename=filename)

    # Clean response
    raw = response.replace("```", "").replace("json", "").strip()
    parsed = json.loads(raw)
    
    return parsed