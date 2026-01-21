"""
Donna Triage - Attachment Analyzer
Decides which AI processor to use based on attachments.
"""
from enum import Enum
from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from ..schema.email_payload import EmailPayload

logger = logging.getLogger(__name__)


class ProcessingStrategy(Enum):
    """
    Processing strategy based on attachment analysis.
    Determines which AI tool to use.
    """
    TEXT_ONLY = "text_only"      # Use CustomCall for text-only processing
    PDF = "pdf"                  # Use CustomCallWithPdf for PDF analysis
    EXCEL = "excel"              # Use Excel processor
    MIXED = "mixed"              # Multiple attachment types - process each


class AttachmentAnalyzer:
    """
    Analyzes email attachments to determine the optimal processing strategy.
    
    Decision Logic:
    ┌─────────────────┬────────────────────┐
    │ Scenario        │ Strategy           │
    ├─────────────────┼────────────────────┤
    │ No attachments  │ TEXT_ONLY          │
    │ Only PDFs       │ PDF                │
    │ Only Excel      │ EXCEL              │
    │ PDF + Excel     │ MIXED              │
    │ Other files     │ TEXT_ONLY          │
    └─────────────────┴────────────────────┘
    """
    
    def analyze(self, email: "EmailPayload") -> ProcessingStrategy:
        """
        Analyze email attachments and return processing strategy.
        
        Args:
            email: The email payload to analyze
            
        Returns:
            ProcessingStrategy indicating which processor to use
        """
        if not email.has_attachments:
            logger.info("📧 No attachments detected -> TEXT_ONLY strategy")
            return ProcessingStrategy.TEXT_ONLY
        
        has_pdf = email.has_pdf
        has_excel = email.has_excel
        
        logger.info(f"📎 Attachments: {email.attachment_names}")
        logger.info(f"   PDF: {has_pdf}, Excel: {has_excel}")
        
        if has_pdf and has_excel:
            logger.info("📊 Mixed attachments -> MIXED strategy")
            return ProcessingStrategy.MIXED
        
        if has_pdf:
            logger.info("📄 PDF detected -> PDF strategy")
            return ProcessingStrategy.PDF
        
        if has_excel:
            logger.info("📗 Excel detected -> EXCEL strategy")
            return ProcessingStrategy.EXCEL
        
        # Other attachment types (images, etc.) - fall back to text
        logger.info("📦 Other attachments -> TEXT_ONLY strategy")
        return ProcessingStrategy.TEXT_ONLY
    
    def should_use_pdf_processor(self, email: "EmailPayload") -> bool:
        """Helper to check if PDF processor should be used."""
        strategy = self.analyze(email)
        return strategy in [ProcessingStrategy.PDF, ProcessingStrategy.MIXED]
    
    def should_use_excel_processor(self, email: "EmailPayload") -> bool:
        """Helper to check if Excel processor should be used."""
        strategy = self.analyze(email)
        return strategy in [ProcessingStrategy.EXCEL, ProcessingStrategy.MIXED]
    
    def get_processing_summary(self, email: "EmailPayload") -> dict:
        """
        Get a summary of the processing decision.
        Useful for logging and debugging.
        """
        strategy = self.analyze(email)
        
        return {
            "strategy": strategy.value,
            "has_attachments": email.has_attachments,
            "attachment_count": len(email.attachments),
            "attachment_names": email.attachment_names,
            "attachment_types": email.attachment_types,
            "use_pdf_processor": strategy in [ProcessingStrategy.PDF, ProcessingStrategy.MIXED],
            "use_excel_processor": strategy in [ProcessingStrategy.EXCEL, ProcessingStrategy.MIXED],
            "use_text_processor": strategy == ProcessingStrategy.TEXT_ONLY
        }
