from io import BytesIO
import zipfile
import logging
import openpyxl

def write_to_excel(data):
    # Create a BytesIO buffer to hold the ZIP file data
    zip_buffer = BytesIO()

    # Create a ZIP archive in the buffer
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for entry in data:
            # Create a new workbook and select the active sheet
            wb = openpyxl.Workbook()
            ws = wb.active
        
            header1 = [
                "VAT exporter",
                "Contact",
                "Commericial reference",
                "Other ref",
                "Freight",
                "Goods location",
                "Export office",
                "Exit office",
                "Name",
                "Street + number",
                "Postcode",
                "city",
                "Country",
                "Inco Term",
                "Place",
                "Container",
                "Truck",
                "Rex/Other"
            ]
        
            address = entry.get('Adrress', "")[0]
            if address:
                name, street, city, code_postal, country = address.get('Company name', ''), address.get('Street', ''), address.get('City', ''), address.get('Postal code', ''), address.get('Country', '') 
                
            if entry.get('Incoterm', ""):
                term, place = entry.get('Incoterm', ('', ''))
                
            Freight = entry.get('Email', '').get('Freight', '')    
        
            values1 = [
                entry.get('Vat', ''),
                entry.get('Principal', ''),
                entry.get('Reference', ''),
                entry.get('Other Ref', ''),
                Freight,
                entry.get('Goods Location', ''),
                entry.get('Export office', ''),
                entry.get('Email', '').get('Exit office', ''),
                name if 'name' in locals() else '',  # Safely handle variables
                street if 'street' in locals() else '',
                code_postal if 'code_postal' in locals() else '',
                city if 'city' in locals() else '',
                country if 'country' in locals() else '',
                term if 'term' in locals() else '',
                place if 'place' in locals() else '',
                entry.get('Container', ''),
                entry.get('wagon', ''),
                entry.get("Customs Code", '')
            ]
        
            header2 = [
                "Commodity",
                "Description",
                "Article",
                "Collis",
                "Gross",
                "Net",
                "Origin",
                "Invoice value",
                "Currency",
                "Statistical Value",
                "Pieces",
                "Invoicenumber",
                "Invoice date",
                "Rex/other"
            ]
            
            rows_entry = []  # To store the processed rows for "items"
            row_empty = []   # To store empty values for non-"items" keys
            
            for key, value in entry.items():
                # Handle array values
                if key == "Items":
                    for obj in value:
                        mini_row = []
                        
                        for ordered_key in header2:
                            # Append the value in the desired order, or an empty string if the key is missing
                            if ordered_key == "Commodity":
                                mini_row.append(obj.get("HS code", ''))
                            elif ordered_key == "Invoice value":
                                mini_row.append(obj.get("Amount", ""))
                            elif ordered_key == "Currency":
                                mini_row.append(entry.get("Currency", ""))
                            elif ordered_key == "Invoicenumber":
                                mini_row.append(obj.get("Inv Ref", ''))
                            elif ordered_key == "Invoice date":
                                mini_row.append(entry.get("Inv Date", ''))
                            elif ordered_key == "Pieces":
                                mini_row.append(obj.get("Qty", ''))
                            elif ordered_key == "Rex/other":
                                mini_row.append(entry.get("Customs Code", ''))
                            else:    
                                mini_row.append(obj.get(ordered_key, ''))
                        rows_entry.append(mini_row)
                else:
                    row_empty.append("")
        
            # Add keys (headers) to the first row
            ws.append(header1)
        
            # Add values to the second row
            ws.append(values1)
        
            # Add empty rows and totals
            ws.append(row_empty)
            ws.append(row_empty)
        
            ws.append(["Total invoices"])
            ws.append([entry.get("Totals")[0].get("Total Amount", 0)])
            ws.append(row_empty)
        
            ws.append(["Total Collis"])
            ws.append([entry.get("Email").get("Collis", 0)])
            ws.append(row_empty)
        
            ws.append(["Total Gross"])
            ws.append([entry.get("Totals")[0].get("Total Gross", 0)])
            ws.append(row_empty)
        
            # Add items
            ws.append(["Items"])
            ws.append(header2)
        
            for arr in rows_entry:
                ws.append(arr)
        
            # Optionally, adjust column widths for better formatting
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter  # Get the column name
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = (max_length + 2)
                ws.column_dimensions[column].width = adjusted_width
        
            # Save the file with the container name
            excel_filename = f"{entry['Reference']}.xlsx"
            with BytesIO() as excel_buffer:
                wb.save(excel_buffer)
                excel_buffer.seek(0)
                zip_file.writestr(excel_filename, excel_buffer.read())
        
    # Finalize the ZIP file and prepare it for the response
    zip_buffer.seek(0)  # Go to the beginning of the ZIP buffer
    return zip_buffer.getvalue()

