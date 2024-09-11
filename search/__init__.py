import azure.functions as func
import logging
import json
import os
import fitz

def search_text_with_coords(pdf_path, search_text):
    results = []
    pdf_document = fitz.open(pdf_path)

    for page in pdf_document:
        blocks = page.get_text("blocks")
        for block in blocks:
            text = block[4]  # Accessing the text content of the block (index 4)
            if search_text in text:
                # Access coordinates by index (avoiding unpacking issue)
                x0 = block[0]
                y0 = block[1]
                x1 = block[2]
                y1 = block[3]

                result = {
                    "text": text,
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                }
                results.append(result)

    return results

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    try:
        text_param = req.form.get('text')
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": "Missing text parameter in the request"}),
            status_code=400,
            mimetype="application/json"
        )

    # Attempt to get files from the request
    try:
        files = req.files.getlist('files')
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": "No file part in the request"}),
            status_code=400,
            mimetype="application/json"
        )

    if not files:
        return func.HttpResponse(
            body=json.dumps({"error": "No selected files"}),
            status_code=400,
            mimetype="application/json"
        )
    
    # Check if text parameter is provided
    if not text_param:
        return func.HttpResponse(
            body=json.dumps({"error": "Text parameter is required"}),
            status_code=400,
            mimetype="application/json"
        )

    extracted_data = []

    for file in files:
        if file.filename == '':
            continue

        # Check if the file is a PDF
        if file and file.filename.endswith('.pdf'):
            # Save the uploaded file temporarily
            uploaded_file_path = './temp/' + file.filename
            with open(uploaded_file_path, 'wb') as temp_file:
                temp_file.write(file.read())
            
        results = search_text_with_coords(uploaded_file_path, text_param)

        # Delete the temporary uploaded file
        os.remove(uploaded_file_path)    

    # Construct the JSON response manually using the `json` module
    response_body = json.dumps({
        "message": results
    })

    return func.HttpResponse(
        body=response_body,
        status_code=200,
        mimetype="application/json"
    )
