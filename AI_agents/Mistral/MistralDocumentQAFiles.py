from io import BufferedReader
import os
import base64
import logging
from mistralai import Mistral
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class MistralDocumentQAFiles:
    def __init__(self, key_vault_url="https://kv-functions-python.vault.azure.net", secret_name="MISTRAL-API-KEY", model="mistral-large-latest"):
        self.key_vault_url = key_vault_url
        self.secret_name = secret_name
        self.model = model
        self.api_key = self._get_api_key_from_key_vault()
        self.client = Mistral(api_key=self.api_key)

    def _get_api_key_from_key_vault(self):
        try:
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=self.key_vault_url, credential=credential)
            api_key = client.get_secret(self.secret_name).value
            return api_key
        except Exception as e:
            logging.error(f"Failed to retrieve Mistral API key from Key Vault: {str(e)}")
            raise

    def upload_base64_pdf(self, base64_pdf: str, filename="uploaded_file.pdf"):
        pdf_bytes = base64.b64decode(base64_pdf)
    
        # ✅ Use /tmp on Azure Functions Linux
        temp_dir = os.getenv("TEMP", "/tmp")
        file_path = os.path.join(temp_dir, filename)
    
        # Write file safely
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
    
        try:
            # Mistral expects an actual file on disk
            with open(file_path, "rb") as file_obj:
                uploaded_pdf = self.client.files.upload(
                    file={
                        "file_name": filename,
                        "content": file_obj,
                    },
                    purpose="ocr"
                )
            signed_url = self.client.files.get_signed_url(file_id=uploaded_pdf.id)
        finally:
            # ✅ Clean up
            os.remove(file_path)
    
        return signed_url.url

    def ask_document(self, base64_pdf: str, prompt: str, filename="uploaded_file.pdf"):
        """Send a prompt and a base64-encoded PDF to the Mistral OCR model and get the answer."""
        document_url = self.upload_base64_pdf(base64_pdf, filename=filename)
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "document_url",
                        "document_url": document_url
                    }
                ]
            }
        ]
        chat_response = self.client.chat.complete(
            model=self.model,
            messages=messages
        )
        return chat_response.choices[0].message.content