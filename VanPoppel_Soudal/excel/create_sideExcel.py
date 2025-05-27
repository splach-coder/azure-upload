import json
from AI_agents.Mistral.MistralDocumentQA import MistralDocumentQA

def extract_clean_excel_from_pdf(base64_pdf: str, filename):
    prompt = (
        "Extract all table data from the PDF text into a clean JSON object.\n\n"
        "- Rows with **two stars \"**\" in a specific column mark a Subtotal row.\n"
        "- Rows with **three stars \"***\" and no other text in that column mark the Grand Total row.\n"
        "- Subtotal rows summarize the section above and include an extra number on the right side called \"Collis\".\n"
        "- Grand Total summarizes the entire table.\n"
        "- Preserve \"Bill. Doc.\" and \"Comm. Code\" columns as strings.\n"
        "- Return only a JSON object with a \"rows\" array.\n"
        "- Mark subtotals with \"SubTotal\": true and add \"Collis\".\n"
        "- Keep row order.\n"
        "- Remove empty or irrelevant rows.\n"
        "- Include references like \"Reference\" if found.\n"
        "- Extract the correct number format for Gross Weight, Net Weight, and Net Value. Detect and convert numbers like 2.240,784 into float format, where the dot is the thousands separator and the comma is the decimal separator (e.g., 2.240,784 → 2240.784).\n\n"
        "**IMPORTANT:** Return ONLY the JSON object with an array named \"rows\". No explanations, no text, no markdown, no formatting."
    )

    # Mistral call
    qa = MistralDocumentQA()
    response = qa.ask_document(base64_pdf, prompt, filename=filename)

    # Clean response
    raw = response.replace("```", "").replace("json", "").strip()
    parsed = json.loads(raw)
    
    return parsed