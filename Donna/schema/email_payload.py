"""
Donna Schema - Email Payload
Data model for incoming email from Logic Apps.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import base64


@dataclass
class Attachment:
    """Represents an email attachment."""
    name: str
    content_type: str
    content_bytes: Optional[str] = None  # Base64 encoded
    size: int = 0
    
    @property
    def is_pdf(self) -> bool:
        """Check if attachment is a PDF."""
        return 'pdf' in self.content_type.lower() or self.name.lower().endswith('.pdf')
    
    @property
    def is_excel(self) -> bool:
        """Check if attachment is an Excel file."""
        excel_types = ['spreadsheet', 'excel', 'xlsx', 'xls', 'csv']
        return any(t in self.content_type.lower() for t in excel_types) or \
               any(self.name.lower().endswith(ext) for ext in ['.xlsx', '.xls', '.csv'])
    
    @property
    def is_image(self) -> bool:
        """Check if attachment is an image."""
        return 'image' in self.content_type.lower()
    
    def get_bytes(self) -> Optional[bytes]:
        """Decode Base64 content to bytes."""
        if self.content_bytes:
            return base64.b64decode(self.content_bytes)
        return None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Attachment":
        """Create Attachment from dictionary."""
        return cls(
            name=data.get('name', 'unknown'),
            content_type=data.get('contentType', data.get('content_type', 'application/octet-stream')),
            content_bytes=data.get('contentBytes', data.get('content_bytes')),
            size=data.get('size', 0)
        )


@dataclass
class EmailPayload:
    """
    Full email data model matching Logic Apps payload.
    
    Expected JSON from Logic App:
    {
        "subject": "...",
        "from": "...",
        "body": "...",
        "bodyPreview": "...",
        "receivedDateTime": "...",
        "importance": "normal",
        "hasAttachments": true,
        "attachments": [{"name": "...", "contentType": "...", "contentBytes": "..."}]
    }
    """
    subject: str
    from_address: str
    body: str
    received_at: str
    attachments: List[Attachment] = field(default_factory=list)
    importance: str = "normal"
    body_preview: str = ""
    to_address: str = ""
    
    @property
    def has_attachments(self) -> bool:
        """Check if email has any attachments."""
        return len(self.attachments) > 0
    
    @property
    def has_pdf(self) -> bool:
        """Check if email has PDF attachments."""
        return any(a.is_pdf for a in self.attachments)
    
    @property
    def has_excel(self) -> bool:
        """Check if email has Excel attachments."""
        return any(a.is_excel for a in self.attachments)
    
    @property
    def attachment_names(self) -> List[str]:
        """Get list of attachment names."""
        return [a.name for a in self.attachments]
    
    @property
    def attachment_types(self) -> List[str]:
        """Get unique list of attachment types (PDF, Excel, Image, Other)."""
        types = set()
        for a in self.attachments:
            if a.is_pdf:
                types.add("PDF")
            elif a.is_excel:
                types.add("Excel")
            elif a.is_image:
                types.add("Image")
            else:
                types.add("Other")
        return list(types)
    
    def get_enriched_text(self) -> str:
        """
        Create enriched text representation for LLM processing.
        Includes all relevant email metadata.
        """
        att_info = ', '.join(self.attachment_names) if self.attachments else 'None'
        
        return f"""
FROM: {self.from_address}
TO: {self.to_address}
SUBJECT: {self.subject}
RECEIVED: {self.received_at}
IMPORTANCE: {self.importance}
HAS ATTACHMENTS: {self.has_attachments}
ATTACHMENT FILES: {att_info}
ATTACHMENT TYPES: {', '.join(self.attachment_types) if self.attachment_types else 'None'}

EMAIL BODY:
{self.body}
""".strip()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmailPayload":
        """
        Create EmailPayload from Logic Apps JSON.
        Handles both camelCase and snake_case field names.
        """
        # Parse attachments
        raw_attachments = data.get('attachments', [])
        attachments = []
        
        if isinstance(raw_attachments, list):
            for att in raw_attachments:
                if isinstance(att, dict):
                    attachments.append(Attachment.from_dict(att))
                elif isinstance(att, str):
                    # Simple string attachment name
                    attachments.append(Attachment(name=att, content_type='application/octet-stream'))
        
        return cls(
            subject=data.get('subject', ''),
            from_address=data.get('from', data.get('from_address', 'Unknown')),
            to_address=data.get('to', data.get('to_address', '')),
            body=data.get('body', data.get('email_body', '')),
            body_preview=data.get('bodyPreview', data.get('body_preview', '')),
            received_at=data.get('receivedDateTime', data.get('received_at', '')),
            importance=data.get('importance', 'normal'),
            attachments=attachments
        )
    
    @classmethod
    def from_request(cls, json_body: Dict[str, Any]) -> "EmailPayload":
        """Alias for from_dict for cleaner API."""
        return cls.from_dict(json_body)
