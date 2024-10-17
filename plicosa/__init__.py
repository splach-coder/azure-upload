import azure.functions as func
import logging
import json
import os
import base64

from plicosa.excel.createExcel import writeExcel
from plicosa.helpers.functions import detect_pdf_type
from plicosa.service.extractors import extract_data_from_pdf, extract_text_from_last_page, extract_text_from_first_page
from plicosa.config.coords import coordinates, coordinates_lastpage, key_map, inv_keyword_params, packingList_keyword_params

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        files = req_body.get('files', [])
    except ValueError:
        logging.error("Invalid JSON in request body.")
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json"
        )
    
    if not files:
        logging.warning("No files provided in the request.")
        return func.HttpResponse(
            body=json.dumps({"error": "No selected files"}),
            status_code=400,
            mimetype="application/json"
        )
    
    data_packinglist = None
    combined_data = None

    for file_info in files:
        file_content_base64 = file_info.get('file')
        filename = file_info.get('filename', 'temp.pdf')

        if not file_content_base64:
            logging.warning(f"File '{filename}' has no content. Skipping.")
            continue
        
        # Decode the base64-encoded content
        try:
            file_content = base64.b64decode(file_content_base64)
        except Exception as e:
            logging.error(f"Failed to decode base64 content for file '{filename}': {e}")
            return func.HttpResponse(
                body=json.dumps({"error": "Failed to decode base64 content", "details": str(e)}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Save the uploaded file temporarily
        temp_dir = os.getenv('TEMP', '/tmp')
        uploaded_file_path = os.path.join(temp_dir, filename)

        # Write the file to the temporary path
        try:
            with open(uploaded_file_path, 'wb') as temp_file:
                temp_file.write(file_content)
            logging.info(f"Saved file '{filename}' to '{uploaded_file_path}'.")
        except Exception as e:
            logging.error(f"Failed to write file '{filename}' to disk: {e}")
            return func.HttpResponse(
                body=json.dumps({"error": "Failed to write file to disk", "details": str(e)}),
                status_code=500,
                mimetype="application/json"
            )

        pdf_type = detect_pdf_type(uploaded_file_path)
        logging.info(f"Detected PDF type for '{filename}': {pdf_type}")

        # Handle the detected PDF type
        if pdf_type == "Packing List":
            extracted_data = extract_data_from_pdf(uploaded_file_path, packingList_keyword_params)
            if not extracted_data:
                logging.error(f"Extraction failed for Packing List PDF: {filename}")
                continue  # Or handle as needed
            try:
                data_packinglist = json.loads(extracted_data)
                logging.info(f"Extracted Packing List data from '{filename}'.")
            except json.JSONDecodeError as jde:
                logging.error(f"JSON decoding failed for Packing List PDF '{filename}': {jde}")
                return func.HttpResponse(
                    body=json.dumps({"error": "Invalid JSON in Packing List PDF", "details": str(jde)}),
                    status_code=400,
                    mimetype="application/json"
                )
        elif pdf_type == "Invoice":
            try:
                data_1 = json.loads(extract_text_from_first_page(uploaded_file_path, coordinates, key_map))
                data_2 = json.loads(extract_text_from_last_page(uploaded_file_path, coordinates_lastpage, ["invoice"]))
                data_3 = json.loads(extract_data_from_pdf(uploaded_file_path, inv_keyword_params))
                combined_data = {**data_1, **data_2, "items": data_3}
                logging.info(f"Extracted Invoice data from '{filename}'.")
            except json.JSONDecodeError as jde:
                logging.error(f"JSON decoding failed for Invoice PDF '{filename}': {jde}")
                return func.HttpResponse(
                    body=json.dumps({"error": "Invalid JSON in Invoice PDF", "details": str(jde)}),
                    status_code=400,
                    mimetype="application/json"
                )
            except Exception as e:
                logging.error(f"Failed to extract Invoice data from '{filename}': {e}")
                return func.HttpResponse(
                    body=json.dumps({"error": "Failed to extract Invoice data", "details": str(e)}),
                    status_code=500,
                    mimetype="application/json"
                )
        else:
            logging.info(f"File '{filename}' is neither Packing List nor Invoice. Skipping.")

    # Validate that both data_packinglist and combined_data are set
    if data_packinglist is None:
        logging.error("Packing List data is missing.")
        return func.HttpResponse(
            body=json.dumps({"error": "Packing List PDF is missing or failed to process"}),
            status_code=400,
            mimetype="application/json"
        )

    if combined_data is None:
        logging.error("Invoice data is missing.")
        return func.HttpResponse(
            body=json.dumps({"error": "Invoice PDF is missing or failed to process"}),
            status_code=400,
            mimetype="application/json"
        )

    # Proceed with data processing
    try:
        # Create a new "items" list, matching based on Batches and DN Nbr
        updated_items = []
        for item in combined_data['items']:
            for entry in data_packinglist:
                if (item.get('Batches:', '') == entry.get('Batch Number:', '')) or (item.get('DN Nbr:', '') == entry.get('Delivery Note', '')):
                    # Merge matching item and entry into one
                    merged_item = {**item, **entry}
                    updated_items.append(merged_item)

        # Update the original dictionary with the new items
        combined_data['items'] = updated_items
        logging.info("Merged Packing List data with Invoice items.")

        # Process the Grand Total and update the items
        for item in combined_data['items']:
            # Split the 'Grand Total' by space and newline
            grand_total_split = item.get('Grand Total', '').replace('\n', ' ').split()

            # Assign the first part to 'quantity', second part to 'gross_weight', and third part to 'net_weight'
            if len(grand_total_split) >= 5:
                item['quantity'] = grand_total_split[0]
                item['gross_weight'] = grand_total_split[2]
                item['net_weight'] = grand_total_split[4]
            else:
                logging.warning(f"Unexpected format in 'Grand Total' for item: {item.get('Grand Total', '')}")

            # Remove the original 'Grand Total' field as it's no longer needed
            item.pop('Grand Total', None)

        # Process 'ship to' field
        ship_to = combined_data.get('ship to', '')
        shipping_address = ship_to.split('\n') if ship_to else []
        if shipping_address:
            combined_data['ship to'] = shipping_address
            logging.info("Processed 'ship to' address.")

        # Initialize totals
        total_gross_weight = 0.0
        total_net_weight = 0.0
        total_quantity = 0.0

        # Iterate over the items and process each one
        for item in combined_data['items']:
            try:
                total_quantity += float(item.get('Total Pallet', '0').replace('.', '').replace(',', '.'))
                total_gross_weight += float(item.get('gross_weight', '0').replace('.', '').replace(',', '.'))
                total_net_weight += float(item.get('net_weight', '0').replace('.', '').replace(',', '.'))
            except ValueError as ve:
                logging.warning(f"Failed to convert values to float for item: {item}. Error: {ve}")

            # Remove unwanted fields from the items
            item.pop('Batch Number:', None)
            item.pop('Delivery Note', None)
            item.pop('Net Weight:', None)
            item.pop('Batches:', None)
            item.pop('DN Nbr:', None)

        # Add the totals to the combined_data dictionary
        combined_data['total_quantity'] = total_quantity
        combined_data['total_gross_weight'] = total_gross_weight
        combined_data['total_net_weight'] = total_net_weight
        logging.info("Calculated totals for quantity, gross weight, and net weight.")

        # Call writeExcel to generate the Excel file in memory
        excel_file = writeExcel(combined_data)
        logging.info("Generated Excel file.")

        # Set response headers for the Excel file download
        headers = {
            'Content-Disposition': 'attachment; filename="invoice_data.xlsx"',
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }

        # Return the Excel file as an HTTP response
        return func.HttpResponse(excel_file.getvalue(), headers=headers, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except TypeError as te:
        logging.error(f"TypeError during processing: {te}")
        return func.HttpResponse(
            body=json.dumps({"error": "Data processing failed due to type error", "details": str(te)}),
            status_code=500,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Unexpected error during processing: {e}")
        return func.HttpResponse(
            body=json.dumps({"error": "An unexpected error occurred", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
