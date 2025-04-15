import azure.functions as func
import logging
import json
import pandas as pd
import io
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from DailyContainerCheck.functions.functions import is_valid_container_number, string_to_unique_array

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

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing file upload request.')

    # Attempt to get the JSON body from the request
    try:
        body = req.get_json()
        data = body.get('data', [])
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid request format"}),
            status_code=400,
            mimetype="application/json"
        )

    if not data:
        return func.HttpResponse(
            body=json.dumps({"error": "No files provided"}),
            status_code=400,
            mimetype="application/json"
        )

    # Load existing records from the blob
    try:
        existing_data, blob_client = load_csv_from_blob()
    except Exception as e:
        logging.error(f"Error loading data from blob: {e}")
        return func.HttpResponse(
            body=json.dumps({"error": "Failed to load existing records from blob."}),
            status_code=500,
            mimetype="application/json"
        )

    queryData = data.get("Table1", [])
    data = []
    wrong_data = []

    for row in queryData:
        containers = row.get("CONTAINERS", "")
        containers = string_to_unique_array(containers)

        data.append({
            "CONTAINERS": containers,
            "DECLARATIONID": row.get("DECLARATIONID", ""),
            "DATEOFACCEPTANCE": row.get("DATEOFACCEPTANCE", ""),
            "TYPEDECLARATIONSSW": row.get("TYPEDECLARATIONSSW", ""),
            "ACTIVECOMPANY": row.get("ACTIVECOMPANY", ""),
            "USERCREATE": row.get("USERCREATE", "")
        })

    for obj in data:
        containers = obj.get("CONTAINERS", "")
        declaration_id = obj.get("DECLARATIONID", "")
        newObj = {**obj}
        newObj["CONTAINERS"] = []

        # Check if DECLARATIONID exists in blob storage
        if float(declaration_id) not in existing_data["ID"].astype(float).values:
            for container in containers:
                container_number_length = len(container)
                # If container length is valid, check further
                if container_number_length != 0:
                    if container_number_length == 11 or container_number_length == 17 or container_number_length == 16:
                        if container_number_length == 11:
                            # Check container validity
                            if not is_valid_container_number(container):
                                newObj["CONTAINERS"].append(container)
                                wrong_data.append(newObj)
                                break  # Break after first invalid container
                    else:
                        # Invalid length containers
                        newObj["CONTAINERS"].append(container)
                        wrong_data.append(newObj)
                        break  # Break after first invalid container

    try:
        return func.HttpResponse(
            json.dumps(wrong_data),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            f"Error processing request: {e}", status_code=500
        )