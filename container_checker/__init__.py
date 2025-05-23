import json
import logging
import azure.functions as func
import pandas as pd
import io
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Key Vault Configuration
key_vault_url = "https://kv-functions-python.vault.azure.net"
secret_name = "azure-storage-account-access-key2"
credential = DefaultAzureCredential()
client = SecretClient(vault_url=key_vault_url, credential=credential)
api_key = client.get_secret(secret_name).value

# Blob Storage Configuration
CONNECTION_STRING = api_key
CONTAINER_NAME = "document-intelligence"
BLOB_NAME = "WRONG_CONTAINERS_CHECKER.csv"

# Load CSV from Blob
def load_csv_from_blob():
    blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=BLOB_NAME)
    stream = blob_client.download_blob().readall()
    return pd.read_csv(io.StringIO(stream.decode("utf-8"))), blob_client

# Main Function
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("API triggered.")
    method = req.method

    df_data, blob_client = load_csv_from_blob()

    # GET /data - Fetch all data from the blob
    if method == "GET":
        response = df_data.to_json(orient="records")
        # Convert JSON string to Python list of dictionaries
        response_list = json.loads(response)
        # Process the response to convert Associated containers to a real list
        processed_response = []
        for item in response_list:
            # Convert the string representation of the list to an actual list
            item['Associated containers'] = json.loads(item['Associated containers'])
            processed_response.append(item)
        return func.HttpResponse(json.dumps(response_list), mimetype="application/json")

    # POST /data - Add new data to the blob or update existing data by ID
    elif method == "POST":
        try:
            new_data = req.get_json()
            record_id = new_data.get("ID")

            if record_id is None:
                return func.HttpResponse("ID is required in the data.", status_code=400)

            # Check if the ID already exists in the records
            if record_id in df_data["ID"].values:
                return func.HttpResponse(f"ID {record_id} already exists. Duplicate IDs are not allowed.", status_code=200)
            
            # Ensure 'Associated containers' is serialized as a JSON string
            if "Associated containers" in new_data:
                associated_containers = new_data["Associated containers"]
                if isinstance(associated_containers, list):
                    new_data["Associated containers"] = json.dumps(associated_containers)
                elif isinstance(associated_containers, str):
                    try:
                        # Validate if it's already a JSON string
                        json.loads(associated_containers)
                    except json.JSONDecodeError:
                        # If not, serialize it
                        new_data["Associated containers"] = json.dumps([associated_containers])
                else:
                    return func.HttpResponse("Invalid format for 'Associated containers'.", status_code=400)

            # Append new record
            df_data = pd.concat([df_data, pd.DataFrame([new_data])], ignore_index=True)
            message = "Data added successfully."

            # Write updated DataFrame back to blob
            output = io.StringIO()
            df_data.to_csv(output, index=False)
            blob_client.upload_blob(output.getvalue(), overwrite=True)

            return func.HttpResponse(message, status_code=201)
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return func.HttpResponse(f"Error: {str(e)}", status_code=400)

    # PATCH /data - Update existing data by ID
    elif method == "PATCH":
        try:
            update_data = req.get_json()
            record_id = update_data.get("ID")
            new_handler = update_data.get("handler")

            if record_id is None:
                return func.HttpResponse(
                    body=json.dumps({"error": "ID is required for update"}),
                    status_code=400,
                    mimetype="application/json"
                )

            if new_handler is None:
                return func.HttpResponse(
                    body=json.dumps({"error": "handler value is required for update"}),
                    status_code=400,
                    mimetype="application/json"
                )
                
            if float(record_id) not in df_data["ID"].values:
                return func.HttpResponse(
                    body=json.dumps({"error": f"Record with ID {record_id} not found"}),
                    status_code=404,
                    mimetype="application/json"
                )

            # Convert record_id to float for comparison
            record_id = float(record_id)
            mask = df_data["ID"].astype(float) == record_id
            df_data.loc[mask, "handler"] = new_handler
            df_data.loc[mask, "handled"] = True

            # Write updated DataFrame back to blob
            output = io.StringIO()
            df_data.to_csv(output, index=False)
            blob_client.upload_blob(output.getvalue(), overwrite=True)

            return func.HttpResponse(
                body=json.dumps({"message": "Record updated successfully"}),
                status_code=200,
                mimetype="application/json"
            )

        except Exception as e:
            logging.error(f"Error during update: {str(e)}")
            return func.HttpResponse(
                body=json.dumps({"error": f"Update failed: {str(e)}"}),
                status_code=500,
                mimetype="application/json"
            )

    return func.HttpResponse("Invalid request", status_code=400)