import datetime
import re
import azure.functions as func
import logging
import json
import os
import base64
import fitz

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.ai.formrecognizer import DocumentAnalysisClient 
from azure.core.credentials import AzureKeyCredential

# --- Imports for Splitting Logic & Your Helpers ---
from AI_agents.Mistral.MistralDocumentQA import MistralDocumentQA
from AI_agents.Gemeni.adress_Parser import AddressParser
from AI_agents.OpenAI.custom_call import CustomCall

from ILS_NUMBER.get_ils_number import call_logic_app
from VanPoppel_Daf.excel.write_to_extra_excel import write_to_extra_excel
from VanPoppel_Daf.excel.create_sideExcel import extract_clean_excel_from_pdf
from VanPoppel_Daf.helpers.functions import clean_incoterm, clean_customs_code, merge_factuur_objects, safe_float_conversion, parse_numbers, parse_weights
from VanPoppel_Daf.excel.create_excel import write_to_excel
from VanPoppel_Daf.zip.create_zip import zip_excels 


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    try:
        req_body = req.get_json()
        files = req_body.get('files', [])
        email_body = req_body.get('body', [])
        subject = req_body.get('subject', '')
    except ValueError:
        return func.HttpResponse(body=json.dumps({"error": "Invalid JSON"}), status_code=400, mimetype="application/json")
    
    if not files:
        return func.HttpResponse(body=json.dumps({"error": "No selected files"}), status_code=400, mimetype="application/json")
        
        
    factuur_results = []
    extra_file_excel_data = None
    
    for file_info in files:
        file_content_base64 = file_info.get('file')
        filename = file_info.get('filename', 'temp.pdf')
           
        extra_file_excel_data = extract_clean_excel_from_pdf(file_content_base64, filename)
        
    try:
        prompt = f"""Your task is to read export instruction email and extract all shipment data into a structured JSON object.

"{email_body}"

The emails are written in Dutch with repeating patterns. Even if some words vary slightly, you must always capture the following fields when present:

Exporter Name (from "Naam afzender/exporteur")

Exporter EORI Number (from "Eori-nummer afzender/exporteur")

Exporter VAT Number (from "Btw-nummer afzender/exporteur")

Invoice Number (from "Factuurnummer")

Unit ID (from "Unit ID")

Partial Shipment (from "Deelzending")

Booking Number (from "boekingsnummer")

Office of Exit (from "Kantoor van uitgang")

Cabins (from lines like "x CABINES")

Gross Weight (kg) (from lines like "BRUTO KG")

Value (€) (from lines like "= €...")

Instructions:

Always output results as a valid JSON object.

If a field is missing, set its value to null.

Normalize numbers (strip units like "KG", "€") but keep them as strings.

If multiple shipments are in the email, return a JSON array of objects (one per shipment).

Do not skip any detail, even if wording or formatting changes.

Example Output:

[
  {
    "Exporter Name": "DAF TRUCKS NV",
    "Exporter EORI Number": "NL801426972",
    "Exporter VAT Number": "BE08766688176",
    "Invoice Number": "58485889",
    "Unit ID": "FZA-70408",
    "Partial Shipment": "Deelzending 2",
    "Booking Number": "PONFEU05219050",
    "Office of Exit": "Via Europort (Rotterdam)",
    "Cabins": "5",
    "Gross Weight (kg)": "7406",
    "Value (€)": "94269.45"
  }
]"""
        call = CustomCall()
        email_data = call.send_request(role="You are an information extraction assistant.", prompt_text=prompt)
        
        merged_result = factuur_results[0]
            
        response = call_logic_app("BESOUDAL", company="vp") 
        if response.get("success"):
            merged_result["ILS_NUMBER"] = response["doss_nr"]
        else:
            logging.error(f"❌ Failed to get ILS_NUMBER: {response.get('error')}")
        
        excel_file = write_to_excel(merged_result)
        reference = "NoRef"
        
        headers = {
            'Content-Disposition': f'attachment; filename="{reference}.zip"',
            'Content-Type': 'application/zip',
            'x-file-type': merged_result.get("File Type", "unknown"),
            'x-factuur-count': str(len(factuur_results))
        }
        return func.HttpResponse(excel_file.getvalue(), headers=headers, mimetype='application/excel', status_code=200)
    
    except Exception as e:
        logging.error(f"Unexpected error during final processing: {e}")
        return func.HttpResponse(body=json.dumps({"error": "An unexpected error occurred during final processing", "details": str(e)}), status_code=500, mimetype="application/json")