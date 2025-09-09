import time
import json
import logging
from openai import OpenAI
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# --- Configuration ---
ASSISTANT_ID = "asst_kEakqjQ22hzMVcuhToFvgMqq"


class PDFInvoiceExtractor:
    def __init__(self, key_vault_url="https://kv-functions-python.vault.azure.net", secret_name="OPENAI-API-KEY"):
        self.key_vault_url = key_vault_url
        self.secret_name = secret_name
        self.api_key = None
        self.client = None
        self.assistant_id = ASSISTANT_ID
        self.initialize_api_key()

    def initialize_api_key(self):
        """Fetch API key from Azure Key Vault and initialize OpenAI client."""
        try:
            credential = DefaultAzureCredential()
            secret_client = SecretClient(vault_url=self.key_vault_url, credential=credential)
            self.api_key = secret_client.get_secret(self.secret_name).value
            self.client = OpenAI(api_key=self.api_key)
            logging.info("✅ OpenAI client initialized")
            return True
        except Exception as e:
            logging.error(f"🔐 Failed to initialize OpenAI client: {str(e)}")
            return False

    def extract_items_from_pdf(self, pdf_path: str, instructions: str = None, timeout: int = 90):
        """Extract items from PDF using the reusable assistant.

        Args:
            pdf_path (str): Path to the PDF file.
            instructions (str, optional): Custom extraction instructions. Defaults to None.
            timeout (int, optional): Max seconds to wait for assistant response. Defaults to 60.
        """

        if not self.client:
            logging.error("🚫 OpenAI client not initialized.")
            return None

        if not instructions:
            instructions = (
    "Your task is to extract *every* invoice item from the attached PDF without skipping or limiting the number of rows.\n"
    "Do not stop after a fixed number of items (like 19). Keep extracting until ALL items from ALL invoice pages are included.\n\n"
    "Output must strictly follow this JSON structure:\n"
    "{\n"
    "  \"Items\": [\n"
    "    {\n"
    "      \"InvoiceNumber\": \"string\",\n"
    "      \"InvoiceDate\": \"dd-mm-yyyy\",\n"
    "      \"Description\": \"string\",\n"
    "      \"HSCode\": \"string\",\n"
    "      \"Origin\": \"string\",\n"
    "      \"NetWeight\": number,\n"
    "      \"Quantity\": number,\n"
    "      \"Amount\": number,\n"
    "      \"Currency\": \"string\"\n"
    "    }\n"
    "  ]\n"
    "}\n\n"
    "Rules:\n"
    "- Dates: dd-mm-yyyy\n"
    "- Numbers: numeric only, dot as decimal separator\n"
    "- Amount must include currency\n"
    "- Extract and combine ALL invoice items from the entire PDF (no omissions, no truncation)\n"
    "- If there are more than 50, 100, or even 1000 items, include them all\n"
    "- Do not summarize or cut off the output\n"
    "- Return ONLY valid JSON with the full list of items."
)

        # --- Upload PDF ---
        with open(pdf_path, "rb") as f:
            uploaded_file = self.client.files.create(file=f, purpose="assistants")

        # --- Create thread ---
        thread = self.client.beta.threads.create()

        # --- Send user message with PDF attachment ---
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=instructions,
            attachments=[{"file_id": uploaded_file.id, "tools": [{"type": "file_search"}]}]
        )

        # --- Run assistant ---
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant_id
        )

        # --- Poll until run is finished (with timeout) ---
        start_time = time.time()
        while run.status in ["queued", "in_progress"]:
            if time.time() - start_time > timeout:
                logging.error("⏳ Run timed out after %s seconds", timeout)
                self.client.files.delete(uploaded_file.id)
                return None
            time.sleep(1)
            run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        # --- Get response ---
        raw = None
        if run.status == "completed":
            messages = self.client.beta.threads.messages.list(thread_id=thread.id)
            for message in messages.data:
                if message.role == "assistant":
                    raw = message.content[0].text.value
                    logging.info("✅ Assistant response received")
                    break
        else:
            logging.error(f"❌ Run failed with status: {run.status}")

        # --- Cleanup (delete uploaded file) ---
        self.client.files.delete(uploaded_file.id)

        if not raw:
            logging.error("❌ No response text available")
            return None

        # --- Extract JSON from response ---
        if "```json" in raw:
            import re
            match = re.search(r"```json\n(.*?)\n```", raw, re.DOTALL)
            if match:
                raw = match.group(1)

        try:
            data = json.loads(raw)
        except Exception:
            logging.error("❌ Failed to parse JSON")
            return None

        return data