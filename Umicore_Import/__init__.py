import azure.functions as func
import logging
import json
import base64
from openai import AsyncOpenAI
import fitz  # PyMuPDF
from io import BytesIO
from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient
import asyncio

from Umicore_Import.helpers.functions import merge_into_items, split_cost_centers, transform_afschrijfgegevens, transform_inklaringsdocument
from Umicore_Import.excel.create_excel import write_to_excel

def is_pdf(filename):
    """Check if file is PDF based on extension"""
    return filename.lower().endswith('.pdf')

def check_filename_pattern(filename):
    """Check if filename contains required patterns"""
    filename_lower = filename.lower()
    if "inklaringsdocument" in filename_lower:
        return "inklaringsdocument"
    elif "afschrijfgegevens" in filename_lower:
        return "afschrijfgegevens"
    return None

async def get_openai_api_key():
    """Fetch OpenAI API key from Azure Key Vault asynchronously"""
    key_vault_url = "https://kv-functions-python.vault.azure.net"
    secret_name = "OPENAI-API-KEY"
    
    credential = None
    client = None
    
    try:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=key_vault_url, credential=credential)
        secret = await client.get_secret(secret_name)
        return secret.value
    except Exception as e:
        logging.error(f"Failed to retrieve OpenAI API key from Key Vault: {str(e)}")
        raise
    finally:
        if client:
            await client.close()
        if credential:
            await credential.close()

async def process_page_with_openai_a(client, text_content, page_num, total_pages):
    """Process a single page with OpenAI API"""
    logging.info(f"Processing page {page_num + 1}/{total_pages}")
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract specific information from customs documents and return as JSON."},
                {"role": "user", "content": f"""Extract the following details from the document and return them as a structured JSON object: 
                {text_content}

                - **VAT Importer**: Extract as a continuous number string without dots or spaces (e.g., "BE0796615072").  
                - **EORI Importer**: Extract as is (e.g., "BECN000016").  
                - **Commercial Reference**: Extract the shipment number (e.g., "51033084").  
                - **Other Reference**: Extract the contract number (e.g., "136818003").  
                - **Incoterm**: Extract the incoterm as uppercase (e.g., "DPU").  
                - **Place**: Extract and return only the city name in uppercase (e.g., "ANTWERP").  
                - **Entrepot**: Extract the reference number for the customs warehouse (e.g., "U-00160-A").  
                - **Commodity**: Extract the goods code (e.g., "8549210000").  
                - **Description**: Extract the first two words of the goods description (e.g., "Elektrisch en elektronische").  
                - **Origin**: Extract the country name and convert it to a 2-letter country code (e.g., "MY" instead of "Malaysia").  
                - **Invoice Value**: Extract and return as a float value (e.g., `1315555.87`).  
                - **Currency**: Extract and return as is (e.g., "EUR").
                - **License**: Extract and return as is (e.g., "ET90.500/12").
                - **Vak 24**: Extract and return as is (e.g., "41").
                - **Vak 37**: Extract and return as is (e.g., "4500").
                - **Vak 44**: Extract and return as is (e.g., "BEVALA00011").
                - **cost center**: Extract and return as is (e.g., "HBN5046").
                

                ### **JSON Output Format:**  
                Return the extracted data in the following format:  
                ```json
                {{
                  "vat_importer": ,
                  "eori_importer": ,
                  "commercial_reference": ,
                  "other_reference": ,
                  "incoterm": ,
                  "place": ,
                  "entrepot": ,
                  "commodity": ,
                  "description": ,
                  "origin":,
                  "invoice_value": ,
                  "currency": 
                  "License" : ,
                  "Vak 24" : ,
                  "Vak 37" : ,
                  "Vak 44" : ,
                  "cost center" : ,
                }}```"""}
            ]
        )
        
        result = response.choices[0].message.content
        
        # Ensure we get valid JSON
        # Find JSON content between triple backticks if present
        import re
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result)
        if json_match:
            result = json_match.group(1)
        
        # Parse the JSON content
        page_data = json.loads(result)
        
        return {
            "page_number": page_num + 1,
            "extracted_data": page_data
        }
        
    except Exception as e:
        logging.error(f"Error processing page {page_num + 1}: {str(e)}")
        return {
            "page_number": page_num + 1,
            "error": str(e)
        }

async def process_page_with_openai_b(client, text_content, page_num, total_pages):
    """Process a single page with OpenAI API"""
    logging.info(f"Processing page {page_num + 1}/{total_pages}")
    
    try:
        prompt = f"""Extract the following details from the document and return them as a structured JSON object:

{text_content}

Kaai: Extract the value after "Kaai:" in uppercase format (e.g., "KAAI 1700").
Agent: Extract the exact value after "Agent:" (e.g., "MSCBEL").
Lloydsnummer: Extract the numerical value after "Lloydsnummer:" (e.g., "9839272").
Verblijfsnummer: Extract the numerical value after "Verblijfsnummer:" (e.g., "293278").
BL: Extract the BL number after "BL:" and return it in uppercase (e.g., "MEDUPQ337602").
Artikel Nummer: Extract the numeric value after "Artikel nummer:" as string (e.g., "0040").
Item: Extract the value following "Item:" (e.g., "001").

Cost Centers: A list of extracted KP sections, each containing relevant details.
For Each Cost Center (KP Section):
For every section starting with KP:, extract:
- KP: The cost center code (e.g., "HBN5101").
- Contract number : The contract number that follows the KP code (e.g., "HBN5101").
- Company: The company name that follows the KP code (e.g., "YOKOHAMA METAL CO LTD").
- Description: The text describing the goods, which follows the company name (e.g., "SWEEPS FROM MIXED ELECTRONIC COMPONENTS").
- Items: A list containing container-specific data.

For Each Container Under a KP:
Extract the container data and ensure proper formatting:
- Container: Extract the container number, remove spaces and special characters (e.g., "TGBU 686125-4" → "TGBU6861254").
- Packages: Extract the number of packages (PK value).
- Gross Weight: Extract the "Bruto kg" value as a number. If the value uses a period as decimal separator (e.g., "7.453"), convert it to a whole number by removing the decimal point (→ 7453). If the value uses a comma as a decimal separator (e.g., "7,453"), interpret it as a floating-point number (→ 7.453).
- Net Weight: Extract the "Netto kg" value as a number. If the value uses a period as decimal separator (e.g., "6.292"), convert it to a whole number by removing the decimal point (→ 6292). If the value uses a comma as a decimal separator (e.g., "6,292"), interpret it as a floating-point number (→ 6.292).

Return the extracted data in the following JSON format:
{{
    "kaai": "",
    "agent": "",
    "lloydsnummer": "",
    "verblijfsnummer": "",
    "bl": "",
    "artikel_nummer": "",
    "item": "",
    "cost_centers": [
        {{
            "kp": "",
            "contract_number": "",
            "company": "",
            "description": "",
            "items": [
                {{
                    "container": "",
                    "packages": 0,
                    "gross_weight": 0,
                    "net_weight": 0
                }}
            ]
        }}
    ]
}}"""

        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract specific information from customs documents and return as JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content
        
        # Ensure we get valid JSON
        # Find JSON content between triple backticks if present
        import re
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result)
        if json_match:
            result = json_match.group(1)
        
        # Parse the JSON content
        page_data = json.loads(result)
        
        return {
            "page_number": page_num + 1,
            "extracted_data": page_data
        }
        
    except Exception as e:
        logging.error(f"Error processing page {page_num + 1}: {str(e)}")
        return {
            "page_number": page_num + 1,
            "error": str(e)
        }

async def process_pdf_with_openai(pdf_content, file_type):
    """Process PDF content with OpenAI API page by page asynchronously"""
    client = None
    doc = None     
    
    try:
        api_key = await get_openai_api_key()
        client = AsyncOpenAI(api_key=api_key)
        
        # Initialize PDF document
        pdf_file = BytesIO(pdf_content)
        doc = fitz.open(stream=pdf_file, filetype="pdf")
        total_pages = len(doc)
        
        # Extract text content from all pages first
        pages_text = []
        for page_num in range(total_pages):
            page = doc[page_num]
            text_content = page.get_text()
            pages_text.append(text_content)
        
        # Close the document after extracting text
        doc.close()
        doc = None
        
        # Create tasks for each page
        tasks = []
        for page_num, text_content in enumerate(pages_text):
            if file_type == "inklaringsdocument":
                tasks.append(process_page_with_openai_a(client, text_content, page_num, total_pages))
            elif file_type == "afschrijfgegevens":
                tasks.append(process_page_with_openai_b(client, text_content, page_num, total_pages))
        
        # Process pages concurrently (with reasonable concurrency)
        pages_data = await asyncio.gather(*tasks)
        
        # Combine results from all pages
        return {
            "total_pages": total_pages,
            "pages": pages_data
        }

    except Exception as e:
        logging.error(f"Error in PDF processing: {str(e)}")
        raise
    finally:
        # Ensure resources are properly closed
        if doc:
            doc.close()
        if client:
            await client.close()

async def process_file(base64_file):
    """Process a single file asynchronously"""
    filename = base64_file.get('filename')
    file_data = base64_file.get('file')

    if not filename or not file_data:
        return None

    # Check if file is PDF and has correct name pattern
    if not is_pdf(filename):
        logging.info(f"Skipping non-PDF file: {filename}")
        return None

    file_type = check_filename_pattern(filename)
    if not file_type:
        logging.info(f"Skipping file with invalid name pattern: {filename}")
        return None

    try:
        # Decode the base64-encoded file
        decoded_data = base64.b64decode(file_data)

        # Process inklaringsdocument with OpenAI
        if file_type == "inklaringsdocument":
            extracted_data = await process_pdf_with_openai(decoded_data, file_type)
            return {
                "filename": filename,
                "type": file_type,
                "data": extracted_data
            }
        elif file_type == "afschrijfgegevens":
            extracted_data = await process_pdf_with_openai(decoded_data, file_type)
            return {
                "filename": filename,
                "type": file_type,
                "data": extracted_data
            }   
        return None

    except Exception as e:
        logging.error(f"Error processing file {filename}: {str(e)}")
        return {
            "filename": filename,
            "type": "error",
            "error": str(e)
        }

async def main_async(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request asynchronously.')

    try:
        body = req.get_json()
        base64_files = body.get('files', [])
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": f"Invalid request format: {str(e)}"}),
            status_code=400,
            mimetype="application/json"
        )

    if not base64_files:
        return func.HttpResponse(
            body=json.dumps({"error": "No files provided"}),
            status_code=400,
            mimetype="application/json"
        )

    try:
        # Process files one by one to avoid resource issues
        processed_results = []
        for base64_file in base64_files:
            result = await process_file(base64_file) 

            if result:
                processed_results.append(result)      

        afschrijfgegevens_data = {}
        inklaringsdocument_data = {}

        for object in processed_results:
            if object.get("type") == "afschrijfgegevens" :
                afschrijfgegevens_data = transform_afschrijfgegevens(object)
            elif object.get("type") == "inklaringsdocument" :
                inklaringsdocument_data = transform_inklaringsdocument(object)

        afschrijfgegevens_data = split_cost_centers(afschrijfgegevens_data)   

        # Merge the objects
        result = merge_into_items(inklaringsdocument_data, afschrijfgegevens_data)
        
        # Calculate totals from the Items list directly
        result["Total packages"] = sum(item.get("packages", 0) for item in result.get("Items", []))
        result["Total gross"] = sum(item.get("gross_weight", 0) for item in result.get("Items", []))
        result["Total net"] = sum(item.get("net_weight", 0) for item in result.get("Items", []))
        result["Total Value"] = sum(item.get("invoice_value", 0) for item in result.get("Items", []))

        try:
            # Call writeExcel to generate the Excel file in memory
            excel_file = write_to_excel(result)
            logging.info("Generated Excel file.")
            
            reference = result.get("commercial_reference", "")

            # Set response headers for the Excel file download
            headers = {
                'Content-Disposition': 'attachment; filename="' + reference + '.xlsx"',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }

            # Return the Excel file as an HTTP response
            return func.HttpResponse(excel_file.getvalue(), headers=headers, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
        except Exception as e:
            logging.error(f"Error: {e}")
            return func.HttpResponse(
                f"Error processing request: {e}", status_code=500
            )   
        
    except Exception as e:
        logging.error("Error during data processing: %s", str(e))
        return func.HttpResponse(
            body=json.dumps({"error": f"Error processing data: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )

# Azure Functions entry point
async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        return await main_async(req)
    except Exception as e:
        logging.error(f"Unhandled exception in main: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )