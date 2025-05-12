import uuid
import azure.functions as func
import logging
import json
import os
import base64
import tempfile

from AI_agents.OpenAI.CustomCallWithImage import CustomCallWithImage

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Lili Maas ZIP Merger - Started.')

    try:
        body = req.get_json()
        base64_files = body.get('files', [])
    except Exception:
        return func.HttpResponse(json.dumps({"error": "Invalid request format"}), status_code=400)

    if not base64_files:
        return func.HttpResponse(json.dumps({"error": "No files provided"}), status_code=400)

    for file in base64_files:
        filename = file.get('filename')
        file_data = file.get('file')
        
        logging.error(f"Processing file: {filename}")

        if not filename.endswith('.zip') or not file_data:
            logging.error(f"Skipping file: {filename} (not a zip or missing data)")
            continue

    try:
        
        res = "res from ai"

        # Set response headers for the Excel file download
        headers = {
            'Content-Disposition': 'attachment; filename="' + res + '.xlsx"',
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }

        # Return the Excel file as an HTTP response
        return func.HttpResponse(excel_file.getvalue(), headers=headers, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            f"Error processing request: {e}", status_code=500
        )