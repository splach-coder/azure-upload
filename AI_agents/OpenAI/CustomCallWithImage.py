from openai import OpenAI
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class CustomCallWithImage:
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
            logging.error(f"🔐 Failed to get API key: {str(e)}")
            return False

    def send_image_prompt(self, image_base64: str, prompt: str) -> str:
        if not self.client:
            logging.error("🚫 OpenAI client not initialized.")
            return None
    
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                temperature=1,
                max_tokens=2048,
                top_p=1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"🔥 Error calling OpenAI with image: {e}")
            return None
   