import azure.functions as func
import logging
import json
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
BLOB_NAME = "declarations-checker/LillyMass-woodpackaging-checker/LILLY_MASS_woodpackaging.csv"

# Load CSV from Blob
def load_csv_from_blob():
    blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=BLOB_NAME)
    stream = blob_client.download_blob().readall()
    return pd.read_csv(io.StringIO(stream.decode("utf-8"))), blob_client

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing DECLARATION ID check.')

    try:
        body = req.get_json()
        declaration_id = str(body.get('declaration_ID', "")).strip()
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid request format"}),
            status_code=400,
            mimetype="application/json"
        )

    if not declaration_id:
        return func.HttpResponse(
            json.dumps({"error": "Missing declaration_ID"}),
            status_code=400,
            mimetype="application/json"
        )

    # Load and check existing data
    try:
        existing_data, blob_client = load_csv_from_blob()
    except Exception as e:
        logging.error(f"Failed to load CSV from blob: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Could not access blob storage"}),
            status_code=500,
            mimetype="application/json"
        )

    # Check if already exists
    if declaration_id in existing_data["declaration_ID"].astype(str).values:
        return func.HttpResponse(
            json.dumps({"send_email": False}),
            status_code=200,
            mimetype="application/json"
        )

    # Append new ID and upload updated file
    try:
        updated_data = pd.concat([existing_data, pd.DataFrame([{"declaration_ID": declaration_id}])], ignore_index=True)
        output = io.StringIO()
        updated_data.to_csv(output, index=False)
        blob_client.upload_blob(output.getvalue(), overwrite=True)

        return func.HttpResponse(
            json.dumps({"send_email": True}),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"❌ Error updating blob: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to update records."}),
            status_code=500,
            mimetype="application/json"
        )
