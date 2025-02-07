import azure.functions as func
import logging
import json

from NCTS_FORMATER.functions.funcitons import combine_jsons_many_to_one_relation, combine_jsons_one_to_many_relation, compare_numbers_with_tolerance, remove_fields_from_json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to parse JSON body
    try:
        req_body = req.get_json()
        file_data = req_body.get('file_data')
        sql_data = req_body.get('sql_data').get('ResultSets').get('Table1')
        email = {
            "sendEmail" : False,
            "emailBody" : ""
        }

        #process the data from the sql if plda files is there
        if len(sql_data)  > 0:
            sql_data = sql_data[0]
            items = sql_data.get("ITEMS")
            items = json.loads(items)
            sql_data["ITEMS"] = items
        else:
            email = {
                "sendEmail" : True,
                "emailBody" : f"""
                <!DOCTYPE html>
                <html>
                <body>
                    <p>Dear,</p>
                    <p>Please check, we can't find the IMAH in the PLDA database:</p>
                    <p><strong>CONTAINER:</strong> {file_data.get("containers")}</p>
                    <p>Best,</p>
                    <p>MESSI10 ⚽</p>
                </body> 
                </html>
                """
            }


        #remove some fields from items in file_Data
        items = file_data.get("items", "")
        cleaned_data = []
        for item in items:
            fields_to_remove = ["packages", "description", "gross weight"]
            cleaned_data.append(remove_fields_from_json(item, fields_to_remove))

        file_data["items"] = cleaned_data

        merged_items = []
        pdf_items = file_data.get("items", "") 
        plda_items = sql_data.get("ITEMS" , "")

        #begin the merging engine
        #ONE TO ONE RELATION
        if len(pdf_items) == 1 and len(plda_items) == 1:
            merged_items = [{**pdf_items[0], **plda_items[0]}]

            PDF_GROSS = file_data.get("globalWeight")
            PDF_PKGS = file_data.get("Package")
            PLDA_GROSS = sql_data.get("CONTROL_GROSSMASS")
            PLDA_PKGS = sql_data.get("CONTROL_PACKAGES")

            if PLDA_PKGS != PDF_PKGS:
                email = {
                "sendEmail" : True,
                "emailBody" : f"""
                <!DOCTYPE html>
                <html>
                <body>
                    <p>Dear,</p>
                    <p>Please check ID {sql_data.get("DECLARATION_ID") }</p>
                    <p><strong>PACKAGE IS DIFFERENT</strong></p>
                    <p>Best,</p>
                    <p>MESSI10 ⚽</p>
                </body>
                </html>
                """
                }
            elif not compare_numbers_with_tolerance(PDF_GROSS, PLDA_GROSS):
                email = {
                "sendEmail" : True,
                "emailBody" : f"""
                <!DOCTYPE html>
                <html>
                <body>
                    <p>Dear,</p>
                    <p>Please check ID {sql_data.get("DECLARATION_ID") }</p>
                    <p><strong>GROSS HAS A DIFFERNECE MORE THAN 5 KG</strong></p>
                    <p>Best,</p>
                    <p>MESSI10 ⚽</p>
                </body>
                </html>
                """
                }

        #ONE TO MANY RELATION
        elif len(pdf_items) == 1 and len(plda_items) >= 1:
            merged_items = combine_jsons_one_to_many_relation(pdf_items[0], plda_items)

            PDF_GROSS = file_data.get("globalWeight")
            PDF_PKGS = file_data.get("Package")
            PLDA_GROSS = sql_data.get("CONTROL_GROSSMASS")
            PLDA_PKGS = sql_data.get("CONTROL_PACKAGES")

            if PLDA_PKGS != PDF_PKGS:
                email = {
                "sendEmail" : True,
                "emailBody" : f"""
                <!DOCTYPE html>
                <html>
                <body>
                    <p>Dear,</p>
                    <p>Please check ID {sql_data.get("DECLARATION_ID") }</p>
                    <p><strong>PACKAGE IS DIFFERENT</strong></p>
                    <p>Best,</p>
                    <p>MESSI10 ⚽</p>
                </body>
                </html>
                """
                }
            elif not compare_numbers_with_tolerance(PDF_GROSS, PLDA_GROSS):
                email = {
                "sendEmail" : True,
                "emailBody" : f"""
                <!DOCTYPE html>
                <html>
                <body>
                    <p>Dear,</p>
                    <p>Please check ID {sql_data.get("DECLARATION_ID") }</p>
                    <p><strong>GROSS HAS A DIFFERNECE MORE THAN 5 KG</strong></p>
                    <p>Best,</p>
                    <p>MESSI10 ⚽</p>
                </body>
                </html>
                """
                }

        #MANY TO ONE RELATION
        elif len(pdf_items) >= 1 and len(plda_items) == 1:
            merged_items = combine_jsons_many_to_one_relation(pdf_items, plda_items[0])

            PDF_GROSS = file_data.get("globalWeight")
            PDF_PKGS = file_data.get("Package")
            PLDA_GROSS = sql_data.get("CONTROL_GROSSMASS")
            PLDA_PKGS = sql_data.get("CONTROL_PACKAGES")

            if PLDA_PKGS != PDF_PKGS:
                email = {
                "sendEmail" : True,
                "emailBody" : f"""
                <!DOCTYPE html>
                <html>
                <body>
                    <p>Dear,</p>
                    <p>Please check ID {sql_data.get("DECLARATION_ID") }</p>
                    <p><strong>PACKAGE IS DIFFERENT</strong></p>
                    <p>Best,</p>
                    <p>MESSI10 ⚽</p>
                </body>
                </html>
                """
                }
            elif not compare_numbers_with_tolerance(PDF_GROSS, PLDA_GROSS):
                email = {
                "sendEmail" : True,
                "emailBody" : f"""
                <!DOCTYPE html>
                <html>
                <body>
                    <p>Dear,</p>
                    <p>Please check ID {sql_data.get("DECLARATION_ID") }</p>
                    <p><strong>GROSS HAS A DIFFERNECE MORE THAN 5 KG</strong></p>
                    <p>Best,</p>
                    <p>MESSI10 ⚽</p>
                </body>
                </html>
                """
                }

        #more cleaning
        cleaned_data2 = []
        for item in merged_items:
            fields_to_remove = ["Packages", "Net Weight", "Gross Weight"]
            cleaned_data2.append(remove_fields_from_json(item, fields_to_remove))

        file_data["items"] = cleaned_data2
        file_data["CONTROL_GROSSMASS"] = sql_data.get("CONTROL_GROSSMASS")
        file_data["CONTROL_NETMASS"] = sql_data.get("CONTROL_NETMASS")
        file_data["CONTROL_PACKAGES"] = sql_data.get("CONTROL_PACKAGES")
        file_data["Email"] = email

        try:
            return func.HttpResponse(
                json.dumps(file_data),
                mimetype="application/json",
                status_code=200
            )

        except Exception as e:
            logging.error(f"Error: {e}")
            return func.HttpResponse(
                f"Error processing request: {e}", status_code=500
            )   

    except ValueError:
        logging.error("Invalid JSON in request body.")
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json"
        )