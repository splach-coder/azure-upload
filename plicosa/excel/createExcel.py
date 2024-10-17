from openpyxl import Workbook
import json
from io import BytesIO
from plicosa.helpers.functions import transform_date

def writeExcel(json_data):
    # If json_data is a string, parse it, otherwise assume it's a dictionary
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data

    # Create a workbook and select the active worksheet
    wb = Workbook()
    ws = wb.active

    # Write invoice details
    ws.append(["VAT", data["Vat"]])
    ws.append(["Inv date", transform_date(data["Inv Date"])])
    ws.append(["Inv Reference", data["Inv Ref"]])
    ws.append(["Ship To", *data["ship to"]])
    ws.append(["Collis", data["total_quantity"]])
    ws.append(["Gross Weight", data["total_gross_weight"]])
    ws.append(["Net Weight", data["total_net_weight"]])
    ws.append(["INCO", *data["Inco"].split(" ")])
    ws.append(["Invoice Amount", *data["invoice"].split(" ")])

    # Add a blank row
    ws.append([])

    # Write header for items
    ws.append(["items"])
    ws.append(["Commodity", "Origin", "Grossweight", "Netweight", "Quantity", "Collis", "Value", "Currency"])

    # Write item details
    for item in data["items"]:
        ws.append([item["Commodity Code of country of dispatch:"], item["Country of Origin: "], item["gross_weight"], item["net_weight"], item["quantity"], item["Total Pallet"], item["Total for the line item"].split(' ')[0], item["Total for the line item"].split(' ')[1]])

    # Save the workbook to a BytesIO object (in memory)
    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    return file_stream