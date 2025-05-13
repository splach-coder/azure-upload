import ast
import azure.functions as func
import logging
import json

from AI_agents.Mistral.MistralDocumentQA import MistralDocumentQA

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

        if (not filename.endswith('.PDF') and not filename.endswith('.pdf')) or not file_data:
            logging.error(f"Skipping file: {filename} (not a pdf or missing data)")
            continue
        
        #detection if the file is a cities certificate
        prompt = (
        "You are an expert in document classification and compliance. "
        "Read the full content of this PDF file and tell me if it contains or references a CITES certificate "
        "(Convention on International Trade in Endangered Species of Wild Fauna and Flora). "
        "Your answer must be: - 'True' if the document contains or mentions a CITES certificate, even partially. "
        "- 'False' if there is no mention or indication of a CITES certificate."
        "Note: The answer must be in JSON format, like this: {'hasCities': True}. No additional text, No text formatting or styling, Just like this {'hasCities': True} bare json."
        )
    
        qa = MistralDocumentQA()  
        answer = qa.ask_document(file_data, prompt, filename=filename)
        answer = answer.replace("```", "")
        answer = answer.replace("json", "")
        answer = ast.literal_eval(answer.strip())
    try:
        
       return func.HttpResponse(
            json.dumps(answer),
            status_code=200,
            mimetype="application/json"
        )
           
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            f"Error processing request: {e}", status_code=500
        )