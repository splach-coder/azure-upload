import logging
import fitz
import re

def extract_container_load_plan_text(pdf_path):
    """
    Filters pages containing 'Invoice & Packing List' and specific fields, then extracts the cleaned text.

    Args:
        pdf_path (str): Path to the input PDF file.

    Returns:
        dict: A dictionary where keys are page numbers (starting from 1) and values are the cleaned page text.
    """
    relevant_pages_text = {}

    with fitz.open(pdf_path) as pdf:
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            text = page.get_text("text")  # Extract full text from the page
            
            # Check if the page contains "Invoice & Packing List" and the specific table fields
            if ("Container Load Plan" in text):
                relevant_pages_text[page_num + 1] = text  # Store text with 1-based page number

    return relevant_pages_text

def extract_cleaned_invoice_text(pdf_path):
    """
    Filters pages containing 'Invoice & Packing List' and specific fields, then extracts the cleaned text.

    Args:
        pdf_path (str): Path to the input PDF file.

    Returns:
        dict: A dictionary where keys are page numbers (starting from 1) and values are the cleaned page text.
    """
    relevant_pages_text = {}

    with fitz.open(pdf_path) as pdf:
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            text = page.get_text("text")  # Extract full text from the page
            
            # Check if the page contains "Invoice & Packing List" and the specific table fields
            if ("Invoice & Packing List" in text):
                relevant_pages_text[page_num + 1] = text  # Store text with 1-based page number

    return relevant_pages_text

def clean_invoice_data(invoice_data):
    """
    Cleans the extracted data by:
    - Extracting and cleaning the invoice number (TM-6numbers).
    - Linking data by invoice number and merging the text across pages.

    Args:
        invoice_data (dict): Extracted data from relevant pages, returned from `extract_cleaned_invoice_text`.

    Returns:
        dict: A dictionary with invoice numbers as keys and the merged data as values.
    """
    # Dictionary to hold the merged data by invoice number
    cleaned_data = {}

    # Iterate over each page's data
    for page_num, text in invoice_data.items():
        # Extract invoice number from the start of the page text
        #invoice_match = re.search(r":\s*(?:TM|CS)-\d{6}\s*No\.", text)  # Match TM-6numbers (e.g., TM-241841)
        invoice_match = re.search(r":\s*((TM|CS)-\d{6})\s*No\.", text) 
        
        if invoice_match:
            # Clean the invoice number
            invoice_number = invoice_match.group(1)  # This will capture the "TM-xxxxxx" part
            cleaned_invoice_number = invoice_number.strip()  # Ensure it's clean (in this case it's already clean)

            # If the invoice number is not in the dictionary, create a new entry
            if cleaned_invoice_number not in cleaned_data:
                cleaned_data[cleaned_invoice_number] = ""

            # Append the page text, joining with a newline between pages
            cleaned_data[cleaned_invoice_number] += text.strip() + "\n"

    return cleaned_data

def get_items_data(text):
    """
    Extracts specific item details from the invoice text:
    - Price
    - Container number
    - HS code
    - Gross weight (G.W.)
    - Net weight (N.W.)
    - Package count
    
    Args:
        text (str): The full text from a page containing item data.

    Returns:
        dict: Extracted data with price, container, hs_code, gross, net, and package count.
    """
    # Define the regex patterns for each field
    price_pattern = r"US\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
    container_pattern = r"([A-Z]{4}\d{7})"
    hs_code_pattern = r"HS Code\s*:\s*(\d{10})"
    
    # Extract each piece of data using the patterns
    price_match = re.search(price_pattern, text)
    container_match = re.search(container_pattern, text)
    hs_code_match = re.search(hs_code_pattern, text)
    
    # Remove the extracted parts from the text for further processing
    if price_match:
        text = text.replace(price_match.group(0), "")
    if container_match:
        text = text.replace(container_match.group(0), "")
    if hs_code_match:
        text = text.replace(hs_code_match.group(0), "")
        
    # Now that the text is cleaned, split it into components (lines or items)
    lines = text.split("\n")
    
    # Extract the gross, net, and package count
    gross, net, pckgs = None, None, None
                
    for i, line in enumerate(lines):
        if "1 - " in line:
            pckgs = lines[i]       
            net = lines[i - 1]       
            gross = lines[i - 2]
            
    gross = gross.replace(",", "")           
    net = net.replace(",", "")           
    pckgs = pckgs.replace(",", "")           
            
    gross = float(gross.strip().replace(',', '')) if gross else 0.00
    net = float(net.strip().replace(',', '')) if net else 0.00
    pckgs = int(pckgs.split(" - ")[1].strip()) if " - " in pckgs else 0         
            
    # Return the final cleaned and structured data
    return {
        "price": float(price_match.group(1).replace(',', '')) if price_match else "",
        "container": container_match.group(1) if container_match else "",
        "hs_code": hs_code_match.group(1) if hs_code_match else "",
        "gross": gross if gross else "",
        "net": net if net else "",
        "pckg": pckgs if pckgs else ""
    }

def extract_items_from_text(text):
    """
    Extracts items from the provided text. Each item starts with 'US$' and ends with 'Container Qty(40HQ):'.

    Args:
        text (str): The full text from which items should be extracted.

    Returns:
        list: A list of extracted items as strings.
    """
    # Split the text by newline characters
    lines = text.split("\n")

    # Join lines back into a single string, so we can work with the full block of text
    full_text = "\n".join(lines)

    # Regex pattern to match the price section that starts with 'US$' and ends with 'Container Qty(40HQ):'
    item_pattern = r"(US\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?.*?Container Qty)"

    # Use regex to find all items matching the pattern
    items = re.findall(item_pattern, full_text, re.DOTALL)

    return items

def clean_and_convert_totals(data):
    """
    Converts the given data dictionary into a list of cleaned dictionaries with numeric fields safely converted.

    Args:
        data (dict): Input dictionary with invoice numbers as keys and lists of values as values.

    Returns:
        list: List of cleaned dictionaries.
    """
    result = []

    # Helper function to safely clean and convert a numeric string
    def safe_convert(value, as_type):
        if not value:
            return 0 if as_type in [int, float] else ""
        try:
            # Remove commas and non-numeric characters except for '.'
            cleaned = re.sub(r"[^\d.]", "", value.replace(",", ""))
            return as_type(cleaned)
        except:
            return 0 if as_type in [int, float] else ""

    # Iterate over each invoice in the data
    for invoice, values in data.items():
        # Extract and clean individual fields
        price = safe_convert(values[0].replace("US$", ""), float) if len(values) > 0 else 0
        pckg = safe_convert(re.search(r"(\d+)\s*CTNS", values[1]).group(1) if len(values) > 1 else "", int)
        pcs = safe_convert(re.search(r"(\d+)\s*PCS|(\d+)\s*SETS", " ".join(values)).group(1) if len(values) > 2 else "", int)
        net = safe_convert(values[3] if len(values) > 3 else "", float)
        gross = safe_convert(values[4] if len(values) > 4 else "", float)

        # Append cleaned data to the result list
        result.append({
            "Invoice_Number": invoice,
            "price": price,
            "pckg": pckg,
            "pcs": pcs,
            "net": net,
            "gross": gross,
        })

    return result

def extract_totals_from_text(text):
    
    lines = {}
    
    # Split the text by newline characters
    for key, txt in text.items():
        lines[key] = txt.split("\n")
        
    totals_lines = {}   
        
     # Split the text by newline characters
    for key, text in lines.items():
        start_idx = -1 
        end_idx = -1 
        for i in range(len(text) - 1, -1, -1):
            if('G.W.' in text[i]):
                end_idx = i
            if('Container Qty' in text[i]):
                start_idx = i
                break
        totals_lines[key] = text[start_idx+1:end_idx]  

    #removes strings from the array leave the number to make sense
    for key, value in totals_lines.items():
        totals_lines[key] = [line for line in value if any(char.isdigit() for char in line)]      
                
    return totals_lines            

def extract_header_details(text):
    first_line = []
    
    # Split the text by newline characters
    for key, txt in text.items():
        first_line = txt.split("\n")
    
    second_line = []     
        
    for key in first_line:
        if(key == "Shipping Per"):
            break
        second_line.append(key)
        
    extracter_data = {}
    
    for item in second_line:
        if 'Date :' in item  :
            year, month, day = item.replace('Date :', '').strip().split('/')
            extracter_data['Date'] = f"{day}/{month}/{year}"
        if 'FOB' in item  :
            term, city = item.strip().split(' ')
            extracter_data['Term'] = [term, city]
            extracter_data['City'] = city
            
    return extracter_data        

def extract_vissel_details(text):
    first_line = []
    
    # Split the text by newline characters
    for key, txt in text.items():
        first_line = txt.split("\n")
    
    vissel = ""    
        
    for i in range(len(first_line)- 1):
        if(first_line[i] == "VESSEL"):
            j = 1
            vissel = first_line[i+j]
            while True:
                if len(vissel) <= 2:
                    j += 1
                    vissel = first_line[i+j]
                else :
                    break    
            
        
    def clean_string(input_string):
        # Use regex to replace anything that is not a letter or space with an empty string
        cleaned_string = re.sub(r'[^a-zA-Z\s]', '', input_string)
        return cleaned_string   
        
    vissel = clean_string(vissel).split(' ')
    
    vissel = [item for item in vissel if len(item) >= 2]
            
    return ' '.join(vissel)
 
def merge_data(data, vissel, header_details):
    # Group data by container
    grouped_data = {}
    
    for item in data:
        container = item['container']
        if container not in grouped_data:
            grouped_data[container] = {'container': container, 'vissel' : vissel, **header_details, 'items': []}
            
        grouped_data[container]['items'].append({
            'Invoice_Number': item['Invoice_Number'],
            'price': item['price'],
            'hs_code': item['hs_code'],
            'gross': item['gross'],
            'net': item['net'],
            'pckg': item['pckg']
        })

    # Convert the grouped data back to a list if needed
    return list(grouped_data.values())

    
    