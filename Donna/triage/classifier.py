"""
Donna Triage - Project Classifier
LLM-powered classification to determine project type.
"""
import json
import logging
import os
from typing import TYPE_CHECKING, Dict, Any, Optional

if TYPE_CHECKING:
    from ..schema.email_payload import EmailPayload
    from ..schema.project_context import ExtractedData

from ..schema.odoo_fields import ProjectType

logger = logging.getLogger(__name__)

# Classification prompt
CLASSIFIER_PROMPT = """You are a project classifier for a logistics software company.
Analyze the email and determine the project type.

PROJECT TYPES:
1. INTERFACE - Data mapping/integration projects:
   - Excel template processing
   - Invoice/document parsing
   - Data transformation (Excel → Custom format)
   - Logistics document handling
   - File format conversions
   
2. AUTOMATION - Process automation projects:
   - Script development
   - Workflow automation
   - API integrations
   - Scheduled tasks
   - Code/development requests

CLASSIFICATION RULES:
- If email mentions Excel, templates, invoices, data mapping → INTERFACE
- If email mentions scripts, automation, workflows, code → AUTOMATION
- If unclear, default to INTERFACE (most common)

OUTPUT FORMAT (JSON only):
{
    "project_type": "INTERFACE" or "AUTOMATION",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation"
}

Return ONLY valid JSON, no markdown.
"""


class ProjectClassifier:
    """
    Uses LLM to classify emails into project types.
    
    The classifier examines:
    - Email subject and body keywords
    - Attachment types
    - Sender patterns
    - Extracted data keywords
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize classifier.
        
        Args:
            llm_client: Optional LLM client. If None, will use CustomCall.
        """
        self.llm = llm_client
        self._init_llm()
    
    def _init_llm(self):
        """Initialize LLM client if not provided."""
        if self.llm is None:
            try:
                from ..openai_api import CustomCall
                self.llm = CustomCall()
            except Exception as e:
                logger.error(f"Failed to initialize LLM client: {e}")
                self.llm = None
    
    def classify(
        self, 
        email: "EmailPayload", 
        extracted: Optional["ExtractedData"] = None
    ) -> ProjectType:
        """
        Classify email into a project type.
        
        Args:
            email: The email payload
            extracted: Optional pre-extracted data from LLM
            
        Returns:
            ProjectType enum value
        """
        # Try LLM classification first
        if self.llm:
            try:
                return self._classify_with_llm(email, extracted)
            except Exception as e:
                logger.warning(f"LLM classification failed, using rules: {e}")
        
        # Fallback to rule-based classification
        return self._classify_with_rules(email, extracted)
    
    def _classify_with_llm(
        self, 
        email: "EmailPayload", 
        extracted: Optional["ExtractedData"] = None
    ) -> ProjectType:
        """Use LLM for classification."""
        context = self._build_context(email, extracted)
        
        response = self.llm.send_request(CLASSIFIER_PROMPT, context)
        
        if not response:
            raise Exception("LLM returned empty response")
        
        # Parse response
        cleaned = response.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        
        project_type_str = data.get("project_type", "INTERFACE").upper()
        confidence = data.get("confidence", 0.5)
        reasoning = data.get("reasoning", "")
        
        logger.info(f"🎯 Classification: {project_type_str} (confidence: {confidence})")
        logger.info(f"   Reasoning: {reasoning}")
        
        try:
            return ProjectType[project_type_str]
        except KeyError:
            logger.warning(f"Unknown project type: {project_type_str}, defaulting to INTERFACE")
            return ProjectType.INTERFACE
    
    def _classify_with_rules(
        self, 
        email: "EmailPayload", 
        extracted: Optional["ExtractedData"] = None
    ) -> ProjectType:
        """Rule-based fallback classification."""
        text = f"{email.subject} {email.body}".lower()
        
        # INTERFACE keywords
        interface_keywords = [
            'excel', 'template', 'invoice', 'mapping', 'data',
            'logistics', 'document', 'pdf', 'format', 'conversion',
            'import', 'export', 'spreadsheet', 'csv'
        ]
        
        # AUTOMATION keywords
        automation_keywords = [
            'script', 'automate', 'automation', 'workflow', 'code',
            'develop', 'api', 'integrate', 'schedule', 'cron',
            'function', 'trigger', 'logic app'
        ]
        
        interface_score = sum(1 for kw in interface_keywords if kw in text)
        automation_score = sum(1 for kw in automation_keywords if kw in text)
        
        # Attachment type also influences classification
        if email.has_excel or email.has_pdf:
            interface_score += 2
        
        logger.info(f"🔍 Rule-based scores - INTERFACE: {interface_score}, AUTOMATION: {automation_score}")
        
        if automation_score > interface_score:
            return ProjectType.AUTOMATION
        
        return ProjectType.INTERFACE  # Default
    
    def _build_context(
        self, 
        email: "EmailPayload", 
        extracted: Optional["ExtractedData"] = None
    ) -> str:
        """Build context string for LLM."""
        keywords = []
        if extracted and extracted.keywords:
            keywords = extracted.keywords
        
        return f"""
Subject: {email.subject}
From: {email.from_address}
Has PDF: {email.has_pdf}
Has Excel: {email.has_excel}
Attachment Types: {', '.join(email.attachment_types)}
Keywords: {', '.join(keywords) if keywords else 'None'}

Body Preview:
{email.body[:1000]}
""".strip()
