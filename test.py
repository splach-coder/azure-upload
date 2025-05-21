import json
import logging
import fitz
import re

def extract_products_from_text(text):
    lines = text.strip().splitlines()
    products = []
    current_block = []

    for line in lines:
        if re.match(r"^\d{7}$", line.strip()):  # new product starts
            if current_block:
                products.append(current_block)
            current_block = [line.strip()]
        elif current_block:
            current_block.append(line.strip())

    if current_block:
        products.append(current_block)

    results = []
    for block in products:
        try:
            # 🩹 Fix broken "Your reference" line
            fixed_block = []
            i = 0
            while i < len(block):
                line = block[i]
                if line.startswith("• Your reference:") and i + 1 < len(block) and not block[i + 1].startswith("•"):
                    line += " " + block[i + 1]
                    i += 1  # skip next line
                fixed_block.append(line)
                i += 1

            block = fixed_block

            product_code = block[0]
            product_name = re.search(r"\• \((.*?)\) (.*)", block[1]).group(2)
            order_number = block[2].split(":")[1].strip()
            reference = block[3].split(":")[1].strip()
            tariff = block[4].split(":")[1].strip()
            net_weight = block[5].split(":")[1].strip()
            surface = block[6].split(":")[1].strip()
            origin = block[7].split(":")[1].strip()

            quantity, unit = block[8].split(" ")
            unit_price = block[9].strip()
            amount = block[10].replace(",", "").strip()

            results.append({
                "product_code": product_code,
                "product_name": product_name,
                "order_number": order_number,
                "reference": reference,
                "customs_tariff": tariff,
                "net_weight": net_weight,
                "surface": surface,
                "origin": origin,
                "quantity": quantity,
                "unit": unit,
                "unit_price": unit_price,
                "amount": amount
            })

        except Exception as e:
            logging.error(f"❌ Error processing block: {block}. Error: {e}")
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
    
with fitz.open("preview.pdf") as doc:
    page_text = doc[0].get_text()
    data = extract_invoice_meta_and_shipping(page_text)
    print(json.dumps(data, indent=4))
