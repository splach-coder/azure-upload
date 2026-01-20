from openai import OpenAI
import logging
import json
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class CustomCallJSON:
    """OpenAI client that enforces JSON output using response_format"""
    
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
            self.client = OpenAI(api_key=self.api_key)
            return True
        except Exception as e:
            logging.error(f"Failed to retrieve OpenAI API key: {str(e)}")
            return False

    def send_request_json(self, role, prompt_text, schema=None):
        """Send request and enforce JSON output"""
        if not self.api_key or not self.client:
            logging.error("OpenAI API client is not initialized")
            return None

        try:
            logging.info(f"Sending request to OpenAI with JSON mode...")
            response = self.client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": role},
                    {"role": "user", "content": prompt_text}
                ],
                response_format={"type": "json_object"},  # Force JSON output
                temperature=0,
                max_tokens=2000
            )
            content = response.choices[0].message.content
            logging.info(f"Received response from OpenAI: {content[:200]}...")
            
            # Parse and return as dict
            parsed = json.loads(content)
            return parsed
            
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from OpenAI response: {e}")
            logging.error(f"Raw content: {content}")
            return None
        except Exception as e:
            logging.error(f"Error while calling OpenAI API: {e}", exc_info=True)
            return None
