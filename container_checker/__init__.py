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
        return func.HttpResponse(df_data.to_json(orient="records"), mimetype="application/json")

    # POST /data - Add new data to the blob
    elif method == "POST":
        try:
            new_data = req.get_json()
            df_data = pd.concat([df_data, pd.DataFrame([new_data])], ignore_index=True)
            blob_client.upload_blob(df_data.to_csv(index=False), overwrite=True)
            return func.HttpResponse("Data added successfully", status_code=201)
        except Exception as e:
            return func.HttpResponse(f"Error: {str(e)}", status_code=400)

    return func.HttpResponse("Invalid request", status_code=400)
