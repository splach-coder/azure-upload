import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from schema.flow_fingerprint import FlowFingerprint

def project_name(flow: FlowFingerprint) -> str:
    """
    Deterministically generates the project name.
    Format: "{Client} – {Flow Type}"
    """
    client = flow.client.strip()
    flow_type = flow.flow_type.strip()
    return f"{client} – {flow_type}"

def project_description(flow: FlowFingerprint) -> str:
    """
    Deterministically generates the project description.
    """
    atts = ", ".join(flow.attachments) if flow.attachments else "None"
    
    desc = f"""
Flow Type: {flow.flow_type}

Source: {flow.source}
Subject Used: {flow.subject_used}
Attachments: {atts}

Logic App: {flow.logic_app}
Azure Function: {flow.azure_function}

PDF Extraction: {flow.pdf_extraction}
Excel Processing: {flow.excel_processing}
LLM Usage: {flow.llm_usage}

Output: {flow.output_format}
""".strip()
    return desc
