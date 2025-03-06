import requests
import json
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from AI_agents.Gemeni.functions.functions import convert_to_list, query_gemini
from bs4 import BeautifulSoup
import re

class EmailParser:
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
        
    def search_for_location(self, email_body: str) -> str:
        """Searches for 'Wijnegem' or 'Maasmechelen' in the email body and returns the found word."""
        # Define the keywords to search for (case-insensitive)
        keywords = ["Wijnegem", "Maasmechelen", "MM", "WY"]

        # Search for keywords in the entire email body
        for keyword in keywords:
            if re.search(rf'\b{keyword}\b', email_body, re.IGNORECASE):
                if keyword == "WY":
                    return "Wijnegem".capitalize()
                elif keyword == "MM":
                    return "Maasmechelen".capitalize()
                else:
                    return keyword.capitalize()

        # Return an empty string if none found
        return ""    
        
    def extract_email_body(self, html_content: str) -> str:
        """Extracts and cleans the main body text from an HTML email."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove unnecessary elements like scripts, styles, and hidden elements
            for tag in soup(['script', 'style', 'head', 'meta', 'link', 'title', '[hidden]']):
                tag.decompose()

            # Extract visible text only
            body_text = soup.get_text(separator='\n', strip=True)

            # Remove excessive whitespace and clean the text
            cleaned_text = '\n'.join(line.strip() for line in body_text.splitlines() if line.strip())

            return cleaned_text

        except Exception as e:
            print(f"Error while extracting email body: {e}")
            return ""    
            
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
            
        prompt = f"""Understand the email well and Extract carefully the following information from the provided email:

            Collis: The number of collis/pallets as a string.
            Weight: The weight as a float, with all formatting cleaned (e.g., "5,610kg" → "5610").
            Exit Office: The exit office code in the format of two letters followed by six numbers (e.g., "FR002300").
            If any field is missing, return an empty string for it.
            Return the result as a Python dictionary with all values as strings.
            Provide only the JSON-like output with no additional text or formatting no json text.

            extract data from here:

            [{address}]"""
        
        try:
            result = query_gemini(self.api_key, prompt)
            result = result.get("candidates")[0].get("content").get("parts")[0].get("text")
            #parsed_address = convert_to_list(result)
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
