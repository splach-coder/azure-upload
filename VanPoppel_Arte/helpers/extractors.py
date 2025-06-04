import json
import re
import logging

from AI_agents.OpenAI.custom_call import CustomCall

def extract_products_from_text(text):
    lines = text.strip().splitlines()
    products = []
    current_block = []

    for line in lines:
        line = line.strip()
        if re.match(r"^\d{7}$", line):  # product code
            if current_block:
                products.append(current_block)
            current_block = [line]
        elif current_block:
            current_block.append(line)

    if current_block:
        products.append(current_block)
    

    results = []
    for block in products:
        try:
            # 🧼 CLEAN unexpected lines (like 'CONSOL')
            expected_prefixes = [
                "• (", "• Order number:", "• Your reference:", "• Customs Tariff:",
                "• Net:", "• Surface:", "• Country of origin:"
            ]
            cleaned_block = [block[0]]  # keep product code

            for line in block[1:]:
                if any(line.startswith(prefix) for prefix in expected_prefixes):
                    cleaned_block.append(line)
                elif re.match(r"^[\d.,]+\s+[A-Z]{1,3}$", line):  # quantity/unit
                    cleaned_block.append(line)
                elif re.match(r"^[\d.,]+\s*EUR$", line):  # full amount
                    cleaned_block.append(line)
                elif re.match(r"^[\d.,]+$", line):  # only the amount (split line)
                    cleaned_block.append(line)
                elif line.strip() == "EUR":  # only currency
                    cleaned_block.append(line)


            # 🩹 Fix broken 'Your reference'
            fixed_block = []
            i = 0
            while i < len(cleaned_block):
                line = cleaned_block[i]
                if line.startswith("• Your reference:") and i + 1 < len(cleaned_block) and not cleaned_block[i + 1].startswith("•"):
                    line += " " + cleaned_block[i + 1]
                    i += 1
                fixed_block.append(line)
                i += 1

            block = fixed_block

            # Validate length
            if len(block) < 11:
                raise ValueError("Block too short after cleaning")

            product_code = block[0]
            product_name = re.search(r"\((.*?)\)\s*(.*)", block[1]).group(2).strip()
            order_number = block[2].split(":", 1)[1].strip()
            reference = block[3].split(":", 1)[1].strip()
            customs_tariff = block[4].split(":", 1)[1].strip()
            net_weight = block[5].split(":", 1)[1].strip()
            surface = block[6].split(":", 1)[1].strip()
            origin = block[7].split(":", 1)[1].strip()

            quantity, unit = block[8].split(" ")
            unit_price = block[9].strip()
            # Handle amount split over two lines (e.g., "2089.34", "EUR")
            amount = None
            if len(block) > 10:
                if re.match(r"^[\d,.]+$", block[10]) and len(block) > 11 and "EUR" in block[11]:
                    amount = block[10].replace(",", "").strip()
                elif "EUR" in block[10]:
                    amount = block[10].replace(",", "").replace("EUR", "").strip()

            results.append({
                "product_code": product_code,
                "product_name": product_name,
                "order_number": order_number,
                "reference": reference,
                "customs_tariff": customs_tariff,
                "net_weight": net_weight,
                "surface": surface,
                "origin": origin,
                "quantity": quantity,
                "unit": unit,
                "unit_price": unit_price,
                "amount": amount
            })

        except Exception as e:
            logging.error(f"Error processing block: {block}. Error: {e}")
            continue

    return results

def extract_invoice_meta_and_shipping(text):
    meta = {}

    # Account Number
    acc_match = re.search(r"Account Number\s+(\d+)", text)
    if acc_match:
        meta["account_number"] = acc_match.group(1)

    # Document Number
    doc_match = re.search(r"Document Number\s+(\d+)", text)
    if doc_match:
        meta["document_number"] = doc_match.group(1)

    # Date
    date_match = re.search(r"Date\s+(\d{2}/\d{2}/\d{4})", text)
    if date_match:
        meta["date"] = date_match.group(1)

    # Shipping Address
    shipping_address = ""
    lines = text.splitlines()
    start_idx = None

    for i, line in enumerate(lines):
        if "Shipping Address" in line:
            start_idx = i + 1
            break

    if start_idx is not None:
        for line in lines[start_idx:]:
            if re.match(r"^\d{7}$", line.strip()):  # product code starts
                break
            shipping_address += line.strip() + "\n"

    meta["shipping_address"] = shipping_address.strip()
    return meta
def extract_totals_and_incoterm(text):
    data = {}
    lines = text.splitlines()

    incoterm = ""
    location = ""

    for i, line in enumerate(lines):
        if "Incoterms:" in line and i > 0:
            incoterm = lines[i - 1].strip()
        if "Location 1:" in line and i > 0:
            location = lines[i - 1].strip()

    if incoterm and location:
        data["incoterm"] = f"{incoterm} {location}"

    # Extract Total incl. VAT
    total_match = re.search(r"Total incl\.?VAT:\s+([\d,.]+)\s+([A-Z]{3})", text)
    if total_match:
        total_str, currency = total_match.groups()
        data["total"] = float(total_str.replace(",", ""))
        data["currency"] = currency

    # Extract Transport value
    transport_pattern = r"Transport\s+([\d,.]+)"
    transport_match = re.search(transport_pattern, text)
    if transport_match:
        transport_str = transport_match.group(1)
        transport_value = float(transport_str.replace(",", ""))
        
        # If transport value is 0.00, check the next line for actual value
        if transport_value == 0.00:
            # Find the position after the matched transport line
            match_end = transport_match.end()
            remaining_text = text[match_end:]
            
            # Look for the next number (potentially with currency)
            next_value_match = re.search(r"\s+([\d,.]+)(?:\s+[A-Z]{3})?", remaining_text)
            if next_value_match:
                next_value_str = next_value_match.group(1)
                try:
                    next_value = float(next_value_str.replace(",", ""))
                    # Only use this value if it's a valid float and not 0
                    if next_value > 0:
                        data["transport"] = next_value
                    else:
                        data["transport"] = transport_value
                except ValueError:
                    # If can't convert to float, use original value
                    data["transport"] = transport_value
            else:
                data["transport"] = transport_value
        else:
            data["transport"] = transport_value

    return data

def extract_customs_authorization_no(text):
    match = re.search(r"customs \s*([A-Z0-9]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def find_page_in_invoice(doc, keywords=["Total incl.VAT:", "Total excl. VAT:", "VAT", "Incoterms:"]):
    try:
        # Open the PDF file
        pdf_document = doc
        
        # Ensure the PDF has at least 1 page
        if len(pdf_document) < 1:
            return "The PDF is empty or has no pages."

        # Search for pages containing all the keywords
        pages_with_data = []
        for page_number in range(len(pdf_document)):
            page = pdf_document[page_number]
            page_text = page.get_text("text")

            # Check if all keywords are found on this page
            if all(keyword in page_text for keyword in keywords):
                pages_with_data.append(page_number + 1)  # Page numbers are 1-based
            
        if pages_with_data:
            return pages_with_data
        else:
            return "No relevant data found in this document."

    except Exception as e:
        return f"An error occurred: {str(e)}"

def extract_customs_code(text_content):
    """Extract customs authorization code from text"""
    custom_call = CustomCall()
    
    # System role for precise extraction
    system_role = """You are a precise data extractor. Extract ONLY the customs authorization code from the text. 
    Return ONLY the code value - no explanations, no labels, no additional text. 
    If no customs authorization code is found, return 'NOT_FOUND'."""
    
    # User prompt
    user_prompt = f"Extract the customs authorization code from this text: {text_content}"
    
    # Send request
    result = custom_call.send_request(system_role, user_prompt)
    
    if result:
        return result.strip()
    else:
        return "EXTRACTION_FAILED"