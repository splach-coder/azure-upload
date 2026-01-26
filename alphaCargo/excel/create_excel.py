from io import BytesIO
import logging
import openpyxl

def safe_get(data, *keys, default=""):
    """Safely get nested keys from a dictionary."""
    temp = data
    for key in keys:
        if isinstance(temp, dict):
            temp = temp.get(key, default)
        else:
            return default
    return temp if temp is not None else default

def write_to_excel(json_string):
    wb = openpyxl.Workbook()
    ws = wb.active
    data = json_string
    
    header1 = [
        "VAT exporter", "EORI importer", "Contact", "Commericial reference",
        "Other ref", "Freight", "Vat cost", "Goods location", "Validation office",
        "Supplier name", "Street + number", "Postcode", "city", "Country",
        "Inco Term", "Place", "ILS number"
    ]
    
    email_data = data.get('Email', {})
    shipment = email_data.get('Shipment', {}) if isinstance(email_data, dict) else {}
    
    ref_dr = safe_get(shipment, 'Reference DR', default='-')
    container = data.get('Container Number', '')
    reference = f"{ref_dr}/{container}"
    
    VatCost = safe_get(email_data, 'Invoice', 'Amount', default=0.00)
    eori_number = safe_get(email_data, 'Client', 'EORI', default="")
    origin = safe_get(shipment, 'Origin Country', default="")
    
    inco_term_list = data.get('Inco Term', ["", ""])
    inco_name = inco_term_list[0] if isinstance(inco_term_list, list) and len(inco_term_list) > 0 else ""
    inco_place = inco_term_list[1] if isinstance(inco_term_list, list) and len(inco_term_list) > 1 else ""

    values1 = [
        data.get('Vat Number', ''),
        eori_number,
        str(data.get('Contact', '')).upper(),
        reference,
        data.get('Invoice Number', ''),
        0.00,
        VatCost,
        '', '', "", "", "", "", "",
        inco_name,
        inco_place,
        '', ''
    ]

    header2 = [
        "Commodity", "Description", "Article", "Collis", "Gross", "Net",
        "Origin", "Invoice value", "Currency", "Pieces", "Invoicenumber",
        "Invoice date", "Container", "Loyds", "Verblijfs", "Agent",
        "article", "Item", "BL"
    ]
    
    ws.append(header1)
    ws.append(values1)
    ws.append([""] * len(header1))
    ws.append([""] * len(header1))
    
    Total = data.get('Total Value', 0)
    total_packages = data.get('Total Packages', 0)
    total_weight_net = data.get('Total Net', 0)
    total_weight_gross = data.get('Total Gross', 0)

    ws.append(["Total invoices"])
    ws.append([round(Total, 2)])
    ws.append([])
    ws.append(["Total Collis"])
    ws.append([total_packages])
    ws.append([])
    ws.append(["Total Gross", "Total Net"])
    ws.append([total_weight_gross, total_weight_net])
    ws.append([])

    ws.append(["Items"])
    ws.append(header2)

    items = data.get("Items", [])
    for obj in items:
        row = []
        for h in header2:
            if h == "Commodity": row.append(obj.get("HS CODE", obj.get("Commodity", "")))
            elif h == "Description": row.append(obj.get("Description", ""))
            elif h == "Gross": row.append(obj.get("Gross Weight", ""))
            elif h == "Net": row.append(obj.get("Net Weight", ""))
            elif h == "Invoice value": row.append(obj.get("Amount", ""))
            elif h == "Collis": row.append(obj.get("Ctns", ""))
            elif h == "Pieces": row.append(obj.get("Quantity", obj.get("Qty", "")))
            elif h == "Invoicenumber": row.append(obj.get("Invoice Number", ""))
            elif h == "Invoice date": row.append(data.get("Invoice Date", ""))
            elif h == "Origin": row.append(origin)
            elif h == "Container": row.append(data.get("Container Number", ""))
            elif h == "Currency": row.append(data.get("Currency", ""))
            else: row.append(obj.get(h, ""))
        ws.append(row)

    # Adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if cell.value and len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except: pass
        ws.column_dimensions[column].width = max_length + 2

    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)
    return file_stream
