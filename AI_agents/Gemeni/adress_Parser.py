import requests
import json
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from AI_agents.Gemeni.functions.functions import convert_to_list, query_gemini
from AI_agents.OpenAI.custom_call import CustomCall

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

    def format_address_to_line_old_addresses(self, address_dict):
        """
        Converts an address dictionary to a single line string.

        Args:
            address_dict (dict): Dictionary containing address components

        Returns:
            str: Single line formatted address
        """
        # Extract address components with empty string as default
        company =  address_dict.get('Company name', '') if address_dict.get('Company name', '')  else address_dict.get('Company', '') 
        street = address_dict.get('Street', '')
        city = address_dict.get('City', '')
        postal_code = address_dict.get('Postal Code', '') if address_dict.get('Postal Code', '') else address_dict.get('Postal code', '')
        country = address_dict.get('Country', '')

        # Build address parts that exist
        address_parts = []
        if company:
            address_parts.append(company)
        if street:
            address_parts.append(street)
        if city:
            address_parts.append(city)
        if postal_code:
            address_parts.append(postal_code)
        if country:
            address_parts.append(country)

        # Join with commas
        return ' '.join(address_parts)

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
            return ['', '', '', '', '']
            
        prompt = f"""Parse the following address into company name, street, city, postal code, and country. Return the result as a Python list with string elements only, without any additional text or code formatting. The country should be represented by its 2-letter abbreviation code. If any field is missing, represent it with an empty string. If city or postal code only those two fields not mentioned find the correct ones from data and add it please. if the country is united kingdom put GB instead of UK.
        the array should be 5 items long, in the order of [company, street, city, postal_code, country_code]
        output should be a python list with string quotes like this and values inside the quotes as python strings ["", "", "", "", ""]
        [{address}]"""
        
        try:
            call = CustomCall()
            result = call.send_request("user", prompt)
            logging.error(result)
            parsed_address = convert_to_list(result)
            return parsed_address
        except requests.exceptions.RequestException as e:
            logging.error(f"Error making request: {e}")
            return ['', '', '', '', '']
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing response: {e}")
            return ['', '', '', '', '']
        except Exception as e:
            logging.error(f"Unexpected error during address parsing: {e}")
            return ['', '', '', '', '']