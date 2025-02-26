import requests
import json
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from AI_agents.Gemeni.functions.functions import convert_to_list, query_gemini

class AddressParser:
    def __init__(self, key_vault_url="https://kv-functions-python.vault.azure.net", secret_name="Gemeni-api-key"):
        """
        Initialize the AddressParser with the Azure Key Vault configuration.
        
        Args:
            key_vault_url (str): URL of the Azure Key Vault
            secret_name (str): Name of the secret containing the Gemini API key
        """
        self.key_vault_url = key_vault_url
        self.secret_name = secret_name
        self.api_key = None
        
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
            list: Parsed address components [company, street, city, postal_code, country_code]
                  or None if parsing failed
        """
        if not self.api_key and not self.initialize_api_key():
            logging.error("No API key available")
            return None
            
        prompt = f"""Parse the following address into company name, street, city, postal code, and country. Return the result as a Python list with string elements only, without any additional text or code formatting. The country should be represented by its 2-letter abbreviation code. If any field is missing, represent it with an empty string.
        [{address}]"""
        
        try:
            result = query_gemini(self.api_key, prompt)
            result = result.get("candidates")[0].get("content").get("parts")[0].get("text")
            parsed_address = convert_to_list(result)
            return parsed_address
        except requests.exceptions.RequestException as e:
            logging.error(f"Error making request: {e}")
            return None
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing response: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error during address parsing: {e}")
            return None

# Example usage
if __name__ == "__main__":
    parser = AddressParser()
    address = "VONIN REFA AS STAKKEVOLLVEIEN 67 TROMSØ NORVÈGE"
    parsed_result = parser.parse_address(address)
    if parsed_result:
        company, street, city, postal_code, country = parsed_result
        print(f"Company: {company}")
        print(f"Street: {street}")
        print(f"City: {city}")
        print(f"Postal Code: {postal_code}")
        print(f"Country: {country}")