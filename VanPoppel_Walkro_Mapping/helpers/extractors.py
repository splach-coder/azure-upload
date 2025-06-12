import json
import logging
from AI_agents.Mistral.MistralDocumentQA import MistralDocumentQA

def extract_clean_excel_from_pdf(base64_pdf: str, filename):
    prompt = (
        """
        Extract the following information from the provided PDF document and format it into a JSON structure. Ensure that all numerical values are in real number format, dates are in the format YYYY-MM-DD, and the country is represented by its country code. Omit any fields that are not present in the document. The JSON should strictly follow the specified format without any additional text or explanations.

        JSON Structure:
        
        Copy
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
              "Gross": "<gross weight as a number>",
              "Net": "<net weight as a number>",
              "Origin": "<origin of goods>",
              "Invoice value": "<invoice value as a number>",
              "Currency": "<currency code>",
              "Invoice number": "<invoice number>",
              "Invoice date": "<invoice date in YYYY-MM-DD format>"
            }
          ]
        }
        
        Instructions:
        
        VAT Exporter: Extract the VAT number and remove any dots or spaces.
        Commercial Reference and Other Ref: Extract the commercial reference number and any other reference numbers.
        Name, Street + Number, Postcode, City, Country: Extract the company's address details. Use the country code for the country.
        Items: For each item in the document, extract the following details:
        Commodity: Extract the HS code as a number.
        Description: Provide a brief description of the commodity.
        Article: Extract the article number.
        Gross and Net: Extract the gross and net weights as numbers.
        Origin: Specify the origin of the goods.
        Invoice Value: Extract the invoice value as a number.
        Currency: Use the currency code.
        Invoice Number and Invoice Date: Extract the invoice number and format the date as YYYY-MM-DD.
        Ensure that the extracted data strictly adheres to the JSON format provided above. Do not include any additional text or explanations in the output.
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