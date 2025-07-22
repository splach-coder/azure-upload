from collections import defaultdict
from datetime import datetime, timedelta
import azure.functions as func
import logging
import json
import pandas as pd
import io
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from performance.functions.functions import calculate_single_user_metrics_fast, count_user_file_creations_last_10_days

# Key Vault Configuration
key_vault_url = "https://kv-functions-python.vault.azure.net"
secret_name = "azure-storage-account-access-key2"
credential = DefaultAzureCredential()
client = SecretClient(vault_url=key_vault_url, credential=credential)
api_key = client.get_secret(secret_name).value

# Blob Storage Configuration
CONNECTION_STRING = api_key
CONTAINER_NAME = "document-intelligence"
PARQUET_BLOB_PATH = "logs/all_data.parquet"
CHECKPOINT_BLOB = "logs/last_checkpoint.txt"
SUMMARY_BLOB = "Dashboard/cache/users_summary.json"

def load_parquet_from_blob():
    try:
        blob_service = BlobServiceClient.from_connection_string(CONNECTION_STRING)
        blob_client = blob_service.get_blob_client(CONTAINER_NAME, PARQUET_BLOB_PATH)
        stream = io.BytesIO()
        blob_client.download_blob().readinto(stream)
        stream.seek(0)
        df = pd.read_parquet(stream)
        return df
    except Exception as e:
        logging.warning(f"No existing parquet found or failed to load: {e}")
        return pd.DataFrame()

def save_parquet_to_blob(df):
    blob_service = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    blob_client = blob_service.get_blob_client(CONTAINER_NAME, PARQUET_BLOB_PATH)
    stream = io.BytesIO()
    df.to_parquet(stream, index=False)
    stream.seek(0)
    blob_client.upload_blob(stream, overwrite=True)

def clear_blob_parquet():
    blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=PARQUET_BLOB_PATH)

    columns = [
    ]

    empty_df = pd.DataFrame(columns=columns)
    buffer = io.BytesIO()
    empty_df.to_parquet(buffer, index=False)
    buffer.seek(0)
    blob_client.upload_blob(buffer, overwrite=True)

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        method = req.method

        if method == "POST":
            body = req.get_json()
            query_data = body.get("data", {}).get("Table1", [])
            new_df = pd.DataFrame(query_data)
            if new_df.empty:
                return func.HttpResponse("No data provided.", status_code=400)

            required_cols = ["DECLARATIONID", "HISTORYDATETIME", "HISTORY_STATUS",
                             "ACTIVECOMPANY", "USERCODE", "TYPEDECLARATIONSSW", "USERCREATE"]
            
            for col in required_cols:
                if col not in new_df.columns:
                    return func.HttpResponse(f"Missing column: {col}", status_code=400)

            if new_df.empty:
                return func.HttpResponse("No allowed users in data.", status_code=400)

            existing_df = load_parquet_from_blob()
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            save_parquet_to_blob(combined_df)

            return func.HttpResponse("✅ Data stored successfully.", status_code=200)

        elif method == "GET":    
            username = req.params.get("user")
            
            if username:
                # Load full data from blob or wherever
                df = load_parquet_from_blob()

                # Call the user metrics function
                metrics = calculate_single_user_metrics_fast(df, username.upper())

                return func.HttpResponse(
                    body=json.dumps(metrics),
                    status_code=200,
                    mimetype="application/json"
                )
            
            # Calculate and return metrics
            df = load_parquet_from_blob()
            if df.empty:
                return func.HttpResponse("No data available to calculate.", status_code=400)

            metrics = count_user_file_creations_last_10_days(df)
            summary_blob = BlobServiceClient.from_connection_string(CONNECTION_STRING)
            blob_client = summary_blob.get_blob_client(CONTAINER_NAME, SUMMARY_BLOB)
            blob_client.upload_blob(json.dumps(metrics, indent=2), overwrite=True)

            return func.HttpResponse(json.dumps(metrics), mimetype="application/json", status_code=200)

        elif method == "DELETE":
            clear_blob_parquet()
            return func.HttpResponse("✅ All data cleared successfully.", status_code=200)
        
        else:
            return func.HttpResponse("Only POST and GET methods supported.", status_code=405)

    except Exception as e:
        logging.error(f"Error in function: {e}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)
