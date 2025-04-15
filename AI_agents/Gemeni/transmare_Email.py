import requests
import json
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from AI_agents.Gemeni.functions.functions import convert_to_list, query_gemini
from bs4 import BeautifulSoup
import re

class TransmareEmailParser:
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
            
    def parse_email(self, address):
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

            Vissel name: The vissel name as a string.
            Exit office: The Exit office as a string (e.g., "FR123456") make sure the exit office is always twochars 6numbers.
            Export kaai: The Export kaai as a string, but in one case if the kaii is begins with K and following by numbers (e.g., K1742) if it's a string don't extract it leave it empty.
            Container Number: The Container Number in the format of four letters followed by seven numbers (e.g., "MSDU7723003").
            Email: this email is forwarded so the body has an email next "From" strings Grab it 
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
