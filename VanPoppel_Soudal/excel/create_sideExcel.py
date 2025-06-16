import json
from AI_agents.Mistral.MistralDocumentQA import MistralDocumentQA

def extract_clean_excel_from_pdf(base64_pdf: str, filename):
    prompt = """
        Extract all table data from the image into a clean JSON object.

        - Rows with **one star "*" in the "Customs cd" column are regular data rows.
        - Rows with **two stars "**" in the "Customs cd" column mark a Subtotal row ("Subtotal": true).
        - Rows with **three stars "***" in the "Customs cd" column mark the GrandTotal row ("GrandTotal": true).
        - If no row contains three stars, treat the last row as the GrandTotal ("GrandTotal": true).
        - Subtotal rows summarize the section above and include an extra value on the right side called "Packages" (highlighted in blue). Extract this value as well.
        - "Packages" is a value outside the table on the same line as the Subtotal rows. Extract it as "Packages".
        - GrandTotal summarizes the entire table.
        - Preserve columns like "Bill. Doc." and "Comm. Code" as strings.
        - Return a clean JSON object with a single key "rows" containing an array of all extracted rows.
        - Mark Subtotal rows with "SubTotal": true and include the "Packages" value.
        - Keep the row order as in the table.
        - Remove empty or irrelevant rows.
        - Convert all number formats correctly:
          - All numbers use European formatting where dot (.) is the thousands separator and comma (,) is the decimal separator.
          - Convert values like '19.751,040' to 19751.040 (float).
          - This applies to Gross, Net weight, and Net Value fields.
          - Gross and Net weight must have 3 decimal places and Net Value must have 2 decimal places.
        - Include any additional fields if present.

        **IMPORTANT:** Return ONLY the final JSON object. No explanations, markdown, or extra formatting.

        Example output:
        {
          "rows": [
            {
              "Customs code": "BEIPOH00058",
              "Bill. Doc.": "97266154",
              "Comm. Code": "32141010",
              "# Collies": 0,
              "Gross": 19751.040,
              "Net weight": 15360.480,
              "WeightUnit": "KG",
              "Net Value": 15360.73,
              "Currency": "GBP",
              "SubTotal": true,
              "Packages": 37
            }
          ]
        }
        """

    # Mistral call
    qa = MistralDocumentQA()
    response = qa.ask_document(base64_pdf, prompt, filename=filename)

    # Clean response
    raw = response.replace("```", "").replace("json", "").strip()
    parsed = json.loads(raw)
    
    return parsed