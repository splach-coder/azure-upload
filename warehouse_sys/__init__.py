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
BLOB_NAME = "DKM_WAREHOUSE_SYSTEM.csv"

# Load CSV from Blob
def load_csv_from_blob():
    blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=BLOB_NAME)
    stream = blob_client.download_blob().readall()
    df = pd.read_csv(io.StringIO(stream.decode("utf-8")))
    return df, blob_client

# Main Function
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("API triggered.")
    method = req.method
    # route: can be "all", "Declarations", "Outbound", or "Inbound"
    route = req.route_params.get("route")
    
    df_data, blob_client = load_csv_from_blob()
    
    # GET: Filter by TYPE if needed
    if method == "GET":
        if not route or route.lower() == "all":
            filtered_df = df_data
        elif route.lower() in ["declaration", "outbound", "inbound"]:
            filtered_df = df_data[df_data["TYPE"].str.lower() == route.lower()]
        else:
            return func.HttpResponse("Invalid route parameter", status_code=400)
        
        response = filtered_df.to_json(orient="records")
        return func.HttpResponse(response, mimetype="application/json")
    
# POST: Create a new record or update TYPE field only
    elif method == "POST":
        try:
            new_data = req.get_json()

            if route and route.lower() == "update":
                # UPDATE operation: Expect an ID and TYPE in the request body
                if "ID" not in new_data:
                    return func.HttpResponse("Missing ID for update", status_code=400)
                if new_data["ID"] not in df_data["ID"].values:
                    return func.HttpResponse("Record not found", status_code=404)
                if "TYPE" not in new_data:
                    return func.HttpResponse("Missing TYPE field for update", status_code=400)
                # Update only the TYPE field
                df_data.loc[df_data["ID"] == new_data["ID"], "TYPE"] = new_data["TYPE"]
                message = "Record updated successfully"

            elif route and route.lower() == "create":
                # CREATE operation: Just add the new record as-is
                df_data = pd.concat([df_data, pd.DataFrame([new_data])], ignore_index=True)
                message = "Record created successfully"

            else:
                return func.HttpResponse("Invalid route for POST. Use 'create' or 'update'.", status_code=400)

            # Write updated CSV back to blob
            blob_client.upload_blob(df_data.to_csv(index=False), overwrite=True)
            return func.HttpResponse(message, status_code=201)
        except Exception as e:
            logging.error(f"Error: {e}")
            return func.HttpResponse(f"Error: {str(e)}", status_code=400)

    return func.HttpResponse("Invalid request", status_code=400)
