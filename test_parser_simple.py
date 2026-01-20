import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AI_agents.ai_odoo_agent.input.email_parser import parse_email_to_flow

email_text = """
Subject: New Project: ACME Invoice Processing

Hi Team,

We need to set up a new flow for ACME Corporation.

They will be sending invoices as PDF attachments via email.
The subject line will contain the invoice reference number.

We need to:
- Extract data using Azure AI Document Intelligence
- Process it through Logic App 'la-acme-invoice-processor'
- Use an Azure Function for validation
- Output should be Excel format

Please set this up ASAP.

Thanks,
Luc
"""

print("Testing email parser...")
try:
    flow = parse_email_to_flow(email_text)
    print(f"✅ SUCCESS!")
    print(f"Client: {flow.client}")
    print(f"Flow Type: {flow.flow_type}")
    print(f"Source: {flow.source}")
    print(f"Output: {flow.output_format}")
except Exception as e:
    print(f"❌ FAILED: {e}")
