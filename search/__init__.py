import base64
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

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body.get('files', [])
    except ValueError:
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json"
        )
    
    if not files:
        return func.HttpResponse(
            body=json.dumps({"error": "No selected files"}),
            status_code=400,
            mimetype="application/json"
        )

    for file in files:
        file_content_base64 = file.get('file')
        text_param = file.get('text')
        filename = file.get('filename', 'temp.pdf')

        if not file_content_base64:
            continue
        
        # Decode the base64-encoded content
        try:
            file_content = base64.b64decode(file_content_base64)
        except Exception as e:
            return func.HttpResponse(
                body=json.dumps({"error": "Failed to decode base64 content", "details": str(e)}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Save the uploaded file temporarily
        temp_dir = os.getenv('TEMP', '/tmp')
        uploaded_file_path = os.path.join(temp_dir, filename)

        # Write the file to the temporary path
        with open(uploaded_file_path, 'wb') as temp_file:
            temp_file.write(file_content)
            
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
