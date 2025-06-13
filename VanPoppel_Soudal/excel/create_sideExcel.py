import json
from AI_agents.Mistral.MistralDocumentQA import MistralDocumentQA

def extract_clean_excel_from_pdf(base64_pdf: str, filename):
    prompt = (
    "Extract all table data from the PDF text into a clean JSON object.\n\n"
    "- Rows with **two stars \"**\" in a specific column mark a Subtotal row (\"Subtotal\": true).\n"
    "- Rows with **three stars \"***\" and no other text in that column mark the GrandTotal row (\"GrandTotal\": true).\n"
    "- If no row contains three stars, treat the last row as the GrandTotal (\"GrandTotal\": true).\n"
    "- Subtotal rows summarize the section above and include an extra value on the right side called \"Collis\".\n"
    "- GrandTotal summarizes the entire table.\n"
    "- Preserve columns like \"Bill. Doc.\" and \"Comm. Code\" as strings.\n"
    "- Return a clean JSON object with a single key \"rows\" containing an array of all extracted rows.\n"
    "- Mark Subtotal rows with \"SubTotal\": true and include the \"Collis\" value.\n"
    "- Keep the row order as in the table.\n"
    "- Remove empty or irrelevant rows.\n"
    "- Include any \"Reference\" fields if present.\n"
    "- Convert all number formats correctly:\n"
    "  → All numbers use European formatting where **dot (.) is the thousands separator** and **comma (,) is the decimal separator**.\n"
    "  → Convert values like '3.694,704' to 3694.704 (float).\n"
    "  → This applies to **Gross**, **Net weight**, and **Net Value** fields.\n"
    "  → **Gross**, **Net weight** must have 3 decimal places and **Net Value** 2 .\n\n"
    "**IMPORTANT:** Return ONLY the final JSON object. No explanations, markdown, or extra formatting.\n\n"
    "Example output:\n"
    "{\n"
    "  \"rows\": [\n"
    "    {\n"
    "      \"Customs code\": \"...\",\n"
    "      \"Bill. Doc.\": \"...\",\n"
    "      \"# Collies\": 12,\n"
    "      \"Gross\": 3694.704,\n"
    "      \"Net weight\": 2290.032,\n"
    "      \"Net Value\": 608.472,\n"
    "      \"Currency\": \"EUR\",\n"
    "      \"Comm. Code\": \"...\",\n"
    "      \"SubTotal\": true\n"
    "    }\n"
    "  ]\n"
    "}"
)


    # Mistral call
    qa = MistralDocumentQA()
    response = qa.ask_document(base64_pdf, prompt, filename=filename)

    # Clean response
    raw = response.replace("```", "").replace("json", "").strip()
    parsed = json.loads(raw)
    
    return parsed