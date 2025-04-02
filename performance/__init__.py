from collections import defaultdict
import azure.functions as func
import logging
import json
import pandas as pd
import io
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from performance.functions.functions import calculate_process_times

# Key Vault Configuration
key_vault_url = "https://kv-functions-python.vault.azure.net"
secret_name = "azure-storage-account-access-key2"
credential = DefaultAzureCredential()
client = SecretClient(vault_url=key_vault_url, credential=credential)
api_key = client.get_secret(secret_name).value

# Blob Storage Configuration
CONNECTION_STRING = api_key
CONTAINER_NAME = "document-intelligence"
BLOB_NAME = "DKM_DECLARATIONS.csv"

# Load CSV from Blob
def load_csv_from_blob():
    blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=BLOB_NAME)
    stream = blob_client.download_blob().readall()
    return pd.read_csv(io.StringIO(stream.decode("utf-8"))), blob_client

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing request. Method: ' + req.method)
    method = req.method

    # GET - Fetch all data from the blob and process it
    if method == "GET":
        try:
            # Load existing records from the blob
            existing_data, blob_client = load_csv_from_blob()
            
            # Group data by DECLARATIONID
            grouped_data = defaultdict(list)
            
            logging.error(grouped_data)

            # Process each row from the existing data
            for _, row in existing_data.iterrows():
                declaration_id = row["DECLARATIONID"]
                
                # Create history entry with all required fields
                history_entry = {
                    "HISTORYDATETIME": row["HISTORYDATETIME"],
                    "HISTORY_STATUS": row["HISTORY_STATUS"],
                    "ACTIVECOMPANY": row["ACTIVECOMPANY"],
                    "USERCODE": row["USERCODE"],
                    "TYPEDECLARATIONSSW": row["TYPEDECLARATIONSSW"]
                }
                
                grouped_data[declaration_id].append(history_entry)

            # Sort history entries by HISTORYDATETIME
            for key in grouped_data:
                grouped_data[key] = sorted(grouped_data[key], key=lambda x: x["HISTORYDATETIME"])

            # Convert to final grouped format
            result = [{"DECLARATIONID": key, "HISTORY": grouped_data[key]} for key in grouped_data]

            # Calculate the required time metrics
            metrics = calculate_process_times(result)
            
            return func.HttpResponse(
                json.dumps(metrics),
                mimetype="application/json",
                status_code=200
            )
        except Exception as e:
            logging.error(f"Error processing GET request: {e}")
            return func.HttpResponse(
                body=json.dumps({"error": "Failed to process data", "details": str(e)}),
                status_code=500,
                mimetype="application/json"
            )
            
    # POST - Insert new data OR fetch specific ID data
    elif method == "POST":
        try:
            # Attempt to get the JSON body from the request
            body = req.get_json()
            data = body.get('data', [])
            
            # Check if ID parameter is provided for fetching specific records
            id_param = body.get('id')
            
            # If ID parameter is provided, fetch data for that ID
            if id_param:
                logging.info(f"Fetching records for ID: {id_param}")
                
                # Load existing records from the blob
                existing_data, blob_client = load_csv_from_blob()
                
                # Filter data for the specific ID
                filtered_data = existing_data[existing_data["DECLARATIONID"] == id_param]
                
                if filtered_data.empty:
                    return func.HttpResponse(
                        body=json.dumps({"message": f"No records found for ID: {id_param}"}),
                        status_code=404,
                        mimetype="application/json"
                    )
                
                # Group data by DECLARATIONID (will be only one in this case)
                grouped_data = defaultdict(list)
                
                # Process each row from the filtered data
                for _, row in filtered_data.iterrows():
                    declaration_id = row["DECLARATIONID"]
                    
                    # Create history entry with all required fields
                    history_entry = {
                        "HISTORYDATETIME": row["HISTORYDATETIME"],
                        "HISTORY_STATUS": row["HISTORY_STATUS"],
                        "ACTIVECOMPANY": row["ACTIVECOMPANY"],
                        "USERCODE": row["USERCODE"],
                        "TYPEDECLARATIONSSW": row["TYPEDECLARATIONSSW"]
                    }
                    
                    grouped_data[declaration_id].append(history_entry)
                
                # Sort history entries by HISTORYDATETIME
                for key in grouped_data:
                    grouped_data[key] = sorted(grouped_data[key], key=lambda x: x["HISTORYDATETIME"])
                
                # Convert to final grouped format
                result = {"DECLARATIONID": id_param, "HISTORY": grouped_data[id_param]}
                
                return func.HttpResponse(
                    body=json.dumps(result),
                    status_code=200,
                    mimetype="application/json"
                )
            
            # If no ID parameter, proceed with normal POST to insert data
            if not data:
                return func.HttpResponse(
                    body=json.dumps({"error": "No data provided"}),
                    status_code=200,
                    mimetype="application/json"
                )

            queryData = data.get("Table1", [])
            
            # Load existing records from the blob
            existing_data, blob_client = load_csv_from_blob()
            
            # Convert incoming data to DataFrame
            new_data = pd.DataFrame(queryData)
            
            # Validate required columns
            required_columns = ["DECLARATIONID", "HISTORYDATETIME", "HISTORY_STATUS", 
                               "ACTIVECOMPANY", "USERCODE", "TYPEDECLARATIONSSW"]
            
            missing_columns = [col for col in required_columns if col not in new_data.columns]
            if missing_columns:
                return func.HttpResponse(
                    body=json.dumps({"error": f"Missing required columns: {missing_columns}"}),
                    status_code=400,
                    mimetype="application/json"
                )
            
            # Combine existing data with new data
            combined_data = pd.concat([existing_data, new_data], ignore_index=True)
            
            # Convert DataFrame back to CSV string
            csv_data = combined_data.to_csv(index=False)
            
            # Upload updated CSV to blob storage
            blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
            blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=BLOB_NAME)
            blob_client.upload_blob(csv_data, overwrite=True)
            
            return func.HttpResponse(
                body=json.dumps({
                    "message": "Data successfully uploaded",
                    "records_added": len(new_data)
                }),
                status_code=200,
                mimetype="application/json"
            )
        except Exception as e:
            logging.error(f"Error processing POST request: {e}")
            return func.HttpResponse(
                body=json.dumps({"error": "Failed to upload data to blob", "details": str(e)}),
                status_code=500,
                mimetype="application/json"
            )
    
    else:
        return func.HttpResponse(
            body=json.dumps({"error": f"Unsupported HTTP method: {method}"}),
            status_code=405,
            mimetype="application/json"
        )