import logging
import azure.functions as func
import pandas as pd
import json
import io
import os
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Key Vault URL
key_vault_url = "https://kv-functions-python.vault.azure.net"
secret_name = "azure-storage-account-access-key2"  # The name of the secret you created

# Use DefaultAzureCredential for authentication
credential = DefaultAzureCredential()

# Create a SecretClient to interact with the Key Vault
client = SecretClient(vault_url=key_vault_url, credential=credential)
# Retrieve the secret value

api_key = client.get_secret(secret_name).value

# 🔗 Azure Blob Storage Connection
CONNECTION_STRING = api_key
CONTAINER_NAME = "document-intelligence"
BALANCE_BLOB = "Employee Balance.csv"
LEAVE_BLOB = "Employee Leave data.csv"
PREDEFINED_HOLIDAYS = "PredefinedHolidays.csv"
REQUESTS_HOLIDAYS = "Holiday Requests List.csv"

def load_csv_from_blob(blob_name):
    """Fetch CSV from Azure Blob Storage and return as DataFrame"""
    blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=blob_name)
    
    stream = blob_client.download_blob().readall()
    return pd.read_csv(io.StringIO(stream.decode("utf-8"))), blob_client

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Employee API triggered.")

    method = req.method
    route = req.route_params.get("route")
    user_id = req.route_params.get("id")  # ID is the user's name

    df_balance, balance_blob_client = load_csv_from_blob(BALANCE_BLOB)
    df_leave, leave_blob_client = load_csv_from_blob(LEAVE_BLOB)
    df_preholidays, preholidays_blob_client = load_csv_from_blob(PREDEFINED_HOLIDAYS)
    df_requests, requests_blob_client = load_csv_from_blob(REQUESTS_HOLIDAYS)

    # **GET /balance** → Get all balances (Manager)
    if method == "GET" and route == "balance" and not user_id:
        return func.HttpResponse(df_balance.to_json(orient="records"), mimetype="application/json")
    
    # **GET /offdays** → Get all offdays (Manager / user)
    if method == "GET" and route == "offdays" and not user_id:
        return func.HttpResponse(df_preholidays.to_json(orient="records"), mimetype="application/json")
    
    # **GET /requests** → Get all requests (Manager / user)
    if method == "GET" and route == "requests" and not user_id:
        return func.HttpResponse(df_requests.to_json(orient="records"), mimetype="application/json")

    # **GET /requests/{id}** → Get balance for one user (User)
    elif method == "GET" and route == "requests" and user_id:
        user_reqs = df_requests[df_requests.get("Employee name", "") == user_id]
        if user_reqs.empty:
            return func.HttpResponse("User not found", status_code=404)
        return func.HttpResponse(user_reqs.to_json(orient="records"), mimetype="application/json")

    # **GET /balance/{id}** → Get balance for one user (User)
    elif method == "GET" and route == "balance" and user_id:
        user_balance = df_balance[df_balance.get("Employee name", "") == user_id]
        if user_balance.empty:
            return func.HttpResponse("User not found", status_code=404)
        return func.HttpResponse(user_balance.to_json(orient="records"), mimetype="application/json")

    # **POST /balance** → Add a new user with balance (Manager)
    elif method == "POST" and route == "balance":
        try:
            new_user = req.get_json()
            df_balance = pd.concat([df_balance, pd.DataFrame([new_user])], ignore_index=True)

            # Save updated balance data to Blob
            balance_blob_client.upload_blob(df_balance.to_csv(index=False), overwrite=True)

            return func.HttpResponse("User added with balance", status_code=201)
        except Exception as e:
            return func.HttpResponse(f"Error: {str(e)}", status_code=400)

    # **GET /leave** → Get all leave data (Manager)
    elif method == "GET" and route == "leave" and not user_id:
        return func.HttpResponse(df_leave.to_json(orient="records"), mimetype="application/json")

    # **GET /leave/{id}** → Get leaves data for multiple user (User)
    elif method == "GET" and route == "leaves" and user_id:
        user_leaves = df_leave[df_leave.get("Team", "") == user_id]
        return func.HttpResponse(user_leaves.to_json(orient="records"), mimetype="application/json")
    
    # **GET /leave/{id}** → Get leave data for one user (User)
    elif method == "GET" and route == "leave" and user_id:
        user_leave = df_leave[df_leave.get("Employee name", "") == user_id]
        if user_leave.empty:
            return func.HttpResponse("User not found", status_code=404)
        return func.HttpResponse(user_leave.to_json(orient="records"), mimetype="application/json")

    # **POST /leave** → Add a new leave request (Both)
    elif method == "POST" and route == "leave":
        try:
            new_leave = req.get_json()
            df_leave = pd.concat([df_leave, pd.DataFrame([new_leave])], ignore_index=True)

            # Save updated leave data to Blob
            leave_blob_client.upload_blob(df_leave.to_csv(index=False), overwrite=True)

            return func.HttpResponse("Leave request added", status_code=201)
        except Exception as e:
            return func.HttpResponse(f"Error: {str(e)}", status_code=400)
        
    # **POST /leave** → Add a new leave request (Both)
    elif method == "POST" and route == "leave":
        try:
            new_leave = req.get_json()

            # Add a default "status" as "pending"
            new_leave["status"] = "pending"

            # Append new leave request to the leave DataFrame
            df_requests = pd.concat([df_requests, pd.DataFrame([new_leave])], ignore_index=True)

            # Save updated leave data to Blob Storage
            requests_blob_client.upload_blob(df_requests.to_csv(index=False), overwrite=True)

            return func.HttpResponse("Leave request added with status 'pending'", status_code=201)
        except Exception as e:
            return func.HttpResponse(f"Error: {str(e)}", status_code=400)

    return func.HttpResponse("Invalid request", status_code=400)