from openai import OpenAI
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class EmailDataExtractor:
    def __init__(self, key_vault_url="https://kv-functions-python.vault.azure.net", secret_name="OPENAI-API-KEY"):
        self.key_vault_url = key_vault_url
        self.secret_name = secret_name
        self.api_key = None
        self.client = None
        self.initialize_api_key()

    def initialize_api_key(self):
        try:
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=self.key_vault_url, credential=credential)
            self.api_key = client.get_secret(self.secret_name).value
            self.client = OpenAI(api_key=self.api_key)  # init OpenAI client here
            return True
        except Exception as e:
            logging.error(f"Failed to retrieve OpenAI API key: {str(e)}")
            return False

    def extract_data_from_email(self, email_text):
        if not self.api_key or not self.client:
            logging.error("OpenAI API client is not initialized")
            return None

        prompt = f"""
        Extract the exit office name as a string from the following email. Only return the office name with no additional text or formatting.

        Email:
        {email_text}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a data extraction assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error while calling OpenAI API: {e}")
            return None
