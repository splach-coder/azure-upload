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


# --- Imports ---
from performance.functions.functions import calculate_single_user_metrics_fast, count_user_file_creations_last_10_days, calculate_all_users_monthly_metrics

# --- Configuration ---
# It's good practice to load these from application settings/environment variables
KEY_VAULT_URL = "https://kv-functions-python.vault.azure.net"
SECRET_NAME = "azure-storage-account-access-key2"

# --- Azure Services Initialization ---
try:
    credential = DefaultAzureCredential()
    kv_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)
    connection_string = kv_client.get_secret(SECRET_NAME).value
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
except Exception as e:
    logging.critical(f"Failed to initialize Azure services: {e}")
    # If the function can't connect to Key Vault or Storage, it cannot operate.
    # In a production scenario, this might trigger an alert.
    connection_string = None 
    blob_service_client = None

# --- Blob Storage Constants ---
CONTAINER_NAME = "document-intelligence"
PARQUET_BLOB_PATH = "logs/all_data.parquet"
SUMMARY_BLOB_PATH = "Dashboard/cache/users_summary.json" # The cache file

# --- Helper Functions ---
def load_parquet_from_blob():
    """Loads the main Parquet file from blob storage into a pandas DataFrame."""
    if not blob_service_client:
        raise ConnectionError("Blob service client is not initialized.")
    try:
        blob_client = blob_service_client.get_blob_client(CONTAINER_NAME, PARQUET_BLOB_PATH)
        stream = io.BytesIO(blob_client.download_blob().readall())
        return pd.read_parquet(stream)
    except Exception as e:
        logging.warning(f"Could not load Parquet file '{PARQUET_BLOB_PATH}'. It may not exist yet. Error: {e}")
        return pd.DataFrame()

def save_json_to_blob(data, blob_path):
    """Saves a JSON object to a specified blob."""
    if not blob_service_client:
        raise ConnectionError("Blob service client is not initialized.")
    try:
        blob_client = blob_service_client.get_blob_client(CONTAINER_NAME, blob_path)
        blob_client.upload_blob(json.dumps(data, indent=2), overwrite=True)
        logging.info(f"Successfully saved JSON to {blob_path}")
    except Exception as e:
        logging.error(f"Failed to save JSON to blob {blob_path}. Error: {e}")
        raise

# --- Main Function App ---
def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main function to handle API requests.
    - GET /api/logs: Returns cached summary data.
    - POST /api/logs/refresh: Recalculates and updates the summary cache.
    - GET /api/logs?user={...}: Returns detailed stats for a single user.
    """
    if not connection_string or not blob_service_client:
        return func.HttpResponse(
            json.dumps({"error": "Backend service not configured."}),
            status_code=503, # Service Unavailable
            mimetype="application/json"
        )

    try:
        method = req.method
        # This will capture 'refresh' from a URL like /api/logs/refresh
        action = req.route_params.get('action')

        # --- Endpoint for Logic App to trigger cache refresh ---
        if method == "POST" and action == "refresh":
            logging.info("Cache refresh process started.")
            
            # 1. Load the latest data from the main Parquet file
            df = load_parquet_from_blob()
            if df.empty:
                logging.warning("Parquet file is empty. Cache will not be updated.")
                return func.HttpResponse(json.dumps({"status": "skipped", "message": "No data available to process."}), status_code=200)

            # 2. Perform the expensive calculation
            metrics = count_user_file_creations_last_10_days(df)
            
            # 3. Save the result to the cache file (users_summary.json)
            save_json_to_blob(metrics, SUMMARY_BLOB_PATH)
            
            logging.info("Cache refresh process completed successfully.")
            return func.HttpResponse(
                json.dumps({"status": "success", "message": "Cache refreshed successfully."}),
                status_code=200,
                mimetype="application/json"
            )

        # --- Endpoint for Frontend to get cached data ---
        elif method == "GET" and not req.params:
            logging.info(f"Request received for cached summary from '{SUMMARY_BLOB_PATH}'.")
            try:
                blob_client = blob_service_client.get_blob_client(CONTAINER_NAME, SUMMARY_BLOB_PATH)
                if not blob_client.exists():
                    return func.HttpResponse(
                        json.dumps({"error": "Cache file not found. Please trigger a refresh."}),
                        status_code=404,
                        mimetype="application/json"
                    )
                
                cached_data = blob_client.download_blob().readall()
                return func.HttpResponse(cached_data, mimetype="application/json", status_code=200)
            except Exception as e:
                logging.error(f"Error reading cache blob: {e}")
                return func.HttpResponse(
                    json.dumps({"error": "Could not read cache file."}),
                    status_code=500,
                    mimetype="application/json"
                )

        # --- Endpoint for detailed user stats (calculated on-the-fly) ---
        elif method == "GET" and req.params.get("user"):
            username = req.params.get("user")
            logging.info(f"Request received for detailed stats for user: {username}")
            df = load_parquet_from_blob()
            if df.empty:
                return func.HttpResponse(json.dumps({"error": "No data available."}), status_code=404)
            
            metrics = calculate_single_user_metrics_fast(df, username.upper())
            return func.HttpResponse(body=json.dumps(metrics), status_code=200, mimetype="application/json")

        # --- Default response for unsupported methods/routes ---
        else:
            return func.HttpResponse("The requested endpoint does not exist or the method is not allowed.", status_code=404)

    except Exception as e:
        logging.error(f"An unexpected error occurred in the main function handler: {e}")
        return func.HttpResponse(json.dumps({"error": "An internal server error occurred."}), status_code=500)
