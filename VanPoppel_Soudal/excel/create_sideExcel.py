import base64
import json
from io import BytesIO
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from AI_agents.Mistral.MistralDocumentQA import MistralDocumentQA

def extract_clean_excel_from_pdf(pdf_path: str) -> BytesIO:
    # Custom prompt
    prompt = (
        "Extract all table data from the PDF text into a clean JSON object.\n\n"
        "Logic for the table rows:\n"
        "- Rows with **two stars \"**\" in a specific column mark a Subtotal row.\n"
        "- Rows with **three stars \"***\" and no other text in that column mark the Grand Total row.\n"
        "- Subtotal rows summarize the section above and include an extra number on the right side called \"Collis\" (number of packages) for that subtotal group.\n"
        "- Grand Total summarizes the entire table.\n"
        "- Normal data rows have no stars and contain detailed item info.\n"
        "- Remove repeated header rows such as \"Customs code\" to avoid duplication.\n"
        "- Treat \"Bill. Doc.\" and \"Comm. Code\" columns as strings, preserving exact formatting.\n"
        "- Capture all columns as keys in each row object.\n"
        "- Mark subtotal rows with \"SubTotal\": true.\n"
        "- Capture the \"collis\" number for subtotal rows as \"Collis\" (number).\n"
        "- Keep the order of rows as in the original table.\n"
        "- Ignore empty or irrelevant rows.\n"
        "- Include overall references if present (e.g., \"Reference\" or \"Export Number\").\n\n"
        "**IMPORTANT:** Return ONLY the JSON object with an array named \"rows\". No explanations, no text, no markdown, no formatting. JUST the raw JSON output."
    )

    # Read PDF and encode to base64
    with open(pdf_path, "rb") as f:
        file_data = base64.b64encode(f.read()).decode("utf-8")

    # Call Mistral QA
    qa = MistralDocumentQA()
    response = qa.ask_document(file_data, prompt, filename=pdf_path)

    # Clean AI response
    raw = response.replace("```", "").replace("json", "").strip()
    parsed = json.loads(raw)

    # Keep only valid items with Comm. Code and remove WeightUnit
    cleaned = [
        {k: v for k, v in row.items() if k != "WeightUnit"}
        for row in parsed["rows"]
        if "Comm. Code" in row
    ]

    # Build headers
    headers = list({k for row in cleaned for k in row.keys()})

    # Create Excel in memory
    wb = Workbook()
    ws = wb.active
    ws.title = "Exported Data"

    for col_num, header in enumerate(headers, 1):
        ws.cell(row=1, column=col_num, value=header)

    for row_num, row_data in enumerate(cleaned, start=2):
        for col_num, header in enumerate(headers, 1):
            ws.cell(row=row_num, column=col_num, value=row_data.get(header, ""))

    # Auto width
    for col_num, header in enumerate(headers, 1):
        col_letter = get_column_letter(col_num)
        ws.column_dimensions[col_letter].width = max(len(header), 15)

    # Save to BytesIO
    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    return file_stream

