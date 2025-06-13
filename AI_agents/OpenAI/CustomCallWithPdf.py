from openai import OpenAI
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class CustomCallWithPdf:
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

    def extract_items_from_pdf(self, pdf_path: str, prompt) -> str:
        """
        Uploads the PDF and sends a prompt to extract item list JSON as per your format.
        Returns the raw JSON string (no extra text).
        """
        if not self.client:
            logging.error("🚫 OpenAI client not initialized.")
            return None

        try:
            with open(pdf_path, "rb") as f:
                uploaded_file = self.client.files.create(file=f, purpose="assistants")

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "file", "file_id": uploaded_file.id}
                        ]
                    }
                ],
                temperature=0,
                max_tokens=2048
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            logging.error(f"🔥 Error extracting items from PDF: {e}")
            return None
