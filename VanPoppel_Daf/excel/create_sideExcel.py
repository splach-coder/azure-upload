import json
from AI_agents.Mistral.MistralDocumentQA import MistralDocumentQA

def extract_clean_excel_from_pdf(base64_pdf: str, filename):
    prompt = """
        Extract all table data from the image into a clean JSON object.

        Row classification rules:
        - Rows with one star "*" in the "Customs cd" column are regular data rows.
        - Rows with two stars "**" in the "Customs cd" column are Subtotal rows. Mark them with "SubTotal": true.
        - Rows with three stars "***" in the "Customs cd" column are the GrandTotal row. Mark it with "GrandTotal": true.
        - If no row contains three stars, treat the last row as the GrandTotal.
        - Subtotal rows summarize the section above and include an extra value on the right side called "Packages" (highlighted in blue). Extract it as an integer under "Packages".

        Data preservation:
        - Preserve all ID-like fields (e.g., "Bill. Doc.", "Comm. Code") as strings with leading zeros intact.
        - Preserve row order from the table.
        - Remove empty or irrelevant rows.

        Numeric conversion rules (MUST be followed exactly):
        - Numeric columns:
          - "Gross": float with exactly 3 decimal places.
          - "Net weight": float with exactly 3 decimal places.
          - "Net Value": float with exactly 2 decimal places.
        - Numbers may use European or other formats:
          - European style: dot (.) is thousands separator, comma (,) is decimal separator.
          - US/other style: comma (,) is thousands separator, dot (.) is decimal separator.
        - Always interpret separators so that:
          - "Gross" and "Net weight" end with exactly 3 decimals.
          - "Net Value" ends with exactly 2 decimals.
        - Rules for separators:
          1. If both "." and "," appear → choose the one that produces the correct number of decimals for that column (3 or 2). The other is a thousands separator.
          2. If only one separator appears:
             - If it has the correct number of digits after it (3 for weights, 2 for value) → it is the decimal separator.
             - Otherwise, it is a thousands separator and must be removed.
          3. If no decimal part is visible → append ".000" for weights or ".00" for value.
        - Always remove thousands separators (., ,, or spaces inside numbers).
        - Sanity check: If Gross < Net weight, re-evaluate separator interpretation until Gross ≥ Net weight.
        - Round half up to the required decimal precision.

        Examples of numeric normalization (input → parsed float):
        - "19.751,040" → 19751.040
        - "1.382,400" → 1382.400
        - "6,336" → 6.336
        - "2,816" → 2.816
        - "19 468,370" → 19468.370
        - "19,468.370" → 19468.370

        Other fields:
        - Add "WeightUnit": "KG" when Gross or Net weight is extracted.
        - Preserve currency codes or symbols if present (e.g., EUR, USD).
        - Include any additional fields if present in the table.

        Output format:
        - Return ONLY the final JSON object.
        - Top-level structure: { "rows": [ ... ] }
        - No explanations, no markdown, no extra text.

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
              "Currency": "EUR",
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