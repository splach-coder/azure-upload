from datetime import datetime
from io import BytesIO
import openpyxl

def write_to_excel(data_entry):
    """Generate and return a single Excel file based on the provided data entry."""
    # Create a new workbook and select the active sheet
    wb = openpyxl.Workbook()
    ws = wb.active

    # Define headers
    header1 = [
        "VAT exporter", "Contact", "Commericial reference", "Other ref", 
        "Freight", "Goods location", "Export office", 
        "Exit office", "Name", "Street + number", 
        "Postcode", "city", "Country", "Inco Term", 
        "Place", "Container", "Truck", "Rex/Other"
    ]

    # Extract and process address details
    data_entry = data_entry[0]
    address = data_entry.get('Address', {})
    name, street, city, code_postal, country = address

    # Extract Incoterm details
    incoterm = data_entry.get('Incoterm', ('', ''))
    term = incoterm[0] if len(incoterm) > 0 else ''
    place = incoterm[1] if len(incoterm) > 1 else ''

    # Prepare header1 row values
    values1 = [
        data_entry.get('Vat Number', ''),
        data_entry.get('Principal', ''),
        data_entry.get('Reference', ''),
        data_entry.get('Other Ref', ''),
        data_entry.get('Email', {}).get('Freight', ''),
        data_entry.get('Email', {}).get('GoodsLocation', ''),
        data_entry.get('Export office', ''),
        data_entry.get('Email', {}).get('Exit Office', ''),
        name,
        street,
        code_postal,
        city,
        country,
        term,
        place,
        data_entry.get('Container', ''),
        data_entry.get('wagon', ''),
        data_entry.get("Customs Code", '')
    ]

    # Prepare items data
    header2 = [
        "Commodity", "Description", "Article", "Collis", "Gross", 
        "Net", "Origin", "Invoice value", "Currency", 
        "Statistical Value", "Pieces", "Invoicenumber", 
        "Invoice date", "Rex/other"
    ]

    rows_entry = []
    items = data_entry.get('Items', [])
    for item in items:
        row = [
            item.get("HS Code", ''),
            item.get("Description", ''),
            item.get("Article", ''),
            item.get("Collis", ''),
            item.get("Gross", ''),
            item.get("Net", ''),
            item.get("COO", ''),
            item.get("Amount", ""),
            data_entry.get("Currency", ""),
            item.get("Statistical Value", ''),
            item.get("Qty", ''),
            item.get("Inv Ref", ''),
        ]
        
        # Process Invoice date
        inv_date_str = data_entry.get("Inv Date", '')
        try:
            inv_date = datetime.strptime(inv_date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
            row.append(inv_date)
        except (ValueError, TypeError):
            row.append(inv_date_str)
        
        row.append(data_entry.get("Customs Code", ''))
        rows_entry.append(row)

    # Write data to the worksheet
    ws.append(header1)
    ws.append(values1)
    ws.append([])  # Empty row
    ws.append([])  # Another empty row

    # Process totals
    ws.append(["Total invoices"])
    ws.append([data_entry.get("Total", 0)])
    ws.append([])  # Empty row

    ws.append(["Total Collis"])
    ws.append([data_entry.get("Email", {}).get("Collis", 0)])
    ws.append([])  # Empty row

    ws.append(["Total Gross"])
    ws.append([data_entry.get("Gross weight Total", 0)])
    ws.append([])  # Empty row

    # Add items
    ws.append(["Items"])
    ws.append(header2)
    for row in rows_entry:
        ws.append(row)

    # Autofit columns
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                cell_length = len(str(cell.value))
                if cell_length > max_length:
                    max_length = cell_length
            except:
                pass
        ws.column_dimensions[column].width = max_length + 2

    # Save workbook to buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()