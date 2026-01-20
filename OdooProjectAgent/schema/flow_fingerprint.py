from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class FlowFingerprint:
    """
    The core data structure that acts as the single source of truth for the Odoo project.
    This structure is strictly deterministic: if two inputs produce the same fingerprint,
    they MUST result in the exact same Odoo project.
    """
    client: str
    flow_type: str

    source: str
    subject_used: bool
    attachments: List[str] = field(default_factory=list)

    logic_app: Optional[str] = None
    azure_function: Optional[str] = None

    pdf_extraction: Optional[str] = None
    excel_processing: Optional[str] = None
    llm_usage: Optional[str] = None

    output_format: str = "Excel"
