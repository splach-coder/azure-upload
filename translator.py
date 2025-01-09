import requests

# Replace these with your actual Consumer-Key and Client Secret
CONSUMER_KEY = 'tGFDDtFNoriSHZw12EmOh9E2tGOwAzuK'
CLIENT_SECRET = 'ZeAxRtJFHa2LE4Ab'

# OAuth 2.0 Token Endpoint
TOKEN_URL = 'https://api.maersk.com/customer-identity/oauth/v2/access_token'

# API Endpoint for Track and Trace Plus
API_URL = 'https://api.maersk.com/synergy/tracking/{container_number}?operator=MAEU'

def get_access_token(consumer_key, client_secret):
    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Consumer-Key': consumer_key
    }
    data = {
        'grant_type': 'client_credentials',
        'client_id': consumer_key,
        'client_secret': client_secret
    }
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    return response.json().get('access_token')

def get_tracking_info(container_number, access_token, consumer_key):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Consumer-Key': consumer_key,
        'Accept': 'application/json'
    }
    url = API_URL.format(container_number=container_number)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    try:
        # Obtain access token
        token = get_access_token(CONSUMER_KEY, CLIENT_SECRET)
        print("Access token obtained successfully.")

        # Replace with your actual container number
        container_number = 'your_container_number'

        # Fetch tracking information
        #tracking_info = get_tracking_info(container_number, token, CONSUMER_KEY)
        print("Tracking Information:")
        #print(tracking_info)

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
