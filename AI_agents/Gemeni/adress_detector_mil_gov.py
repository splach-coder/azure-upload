import requests
import json
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from AI_agents.Gemeni.functions.functions import convert_to_list, query_gemini

class AddressDetector:
    def __init__(self, key_vault_url="https://kv-functions-python.vault.azure.net", secret_name="Gemeni-api-key"):
        """
        Initialize the AddressDetector with the Azure Key Vault configuration.
        
        Args:
            key_vault_url (str): URL of the Azure Key Vault
            secret_name (str): Name of the secret containing the Gemini API key
        """
        self.key_vault_url = key_vault_url
        self.secret_name = secret_name
        self.api_key = None
        self.initialize_api_key()
        
    def initialize_api_key(self):
        """
        Retrieve the Gemini API key from Azure Key Vault.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Use DefaultAzureCredential for authentication
            credential = DefaultAzureCredential()
            # Create a SecretClient to interact with the Key Vault
            client = SecretClient(vault_url=self.key_vault_url, credential=credential)
            # Retrieve the secret value
            self.api_key = client.get_secret(self.secret_name).value
            return True
        except Exception as e:
            logging.error(f"Failed to retrieve secret: {str(e)}")
            return False
        
    def parse_address(self, address):
        """
        Parse an address string into structured components using Gemini API.
        
        Args:
            address (str): The address to parse
            
        Returns:
            str: "Yes" if the address is related to a military or government entity, "No" otherwise.
                  or None if parsing failed
        """
        if not self.api_key:
            logging.error("No API key available")
            return None
            
        prompt = f"""
            Given an address, determine whether it belongs to a military or government entity.

            If the address is related to the military (Army, Navy, Air Force, etc.) or a government building, respond with "Yes".
            Otherwise, respond with "No".
            Provide no explanations—just "Yes" or "No".

            Example Inputs:
                "Pentagon, Arlington, VA, USA" → "Yes"
                "1600 Pennsylvania Ave NW, Washington, DC" → "Yes"
                "123 Main Street, New York, NY" → "No"

        [{address}]"""
        
        try:
            result = query_gemini(self.api_key, prompt)
            result = result.get("candidates")[0].get("content").get("parts")[0].get("text")
            return result
        except requests.exceptions.RequestException as e:
            logging.error(f"Error making request: {e}")
            return None
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing response: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error during address parsing: {e}")
            return None

