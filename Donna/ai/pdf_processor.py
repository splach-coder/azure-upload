"""
Donna AI - PDF Processor
Wrapper for CustomCallWithPdf to process PDF attachments.
"""
import json
import logging
import os
import sys
import tempfile
import base64
from typing import Dict, Any, Optional, List

from .prompt_router import PromptRouter

logger = logging.getLogger(__name__)


class PdfProcessor:
    """
    Processes PDF attachments using CustomCallWithPdf (OpenAI Assistants API).
    
    Used when:
    - Email contains PDF attachments
    - PDF content analysis is needed
    """
    
    def __init__(self, pdf_client=None, prompt_router: Optional[PromptRouter] = None):
        """
        Initialize PDF processor.
        
        Args:
            pdf_client: Optional PDF client (PDFInvoiceExtractor)
            prompt_router: Optional prompt router
        """
        self.pdf_client = pdf_client
        self.prompt_router = prompt_router or PromptRouter()
        self._init_client()
    
    def _init_client(self):
        """Initialize PDF client if not provided."""
        if self.pdf_client is None:
            try:
                from ..openai_api import PDFInvoiceExtractor
                self.pdf_client = PDFInvoiceExtractor()
                logger.info("✅ PdfProcessor client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize PDF client: {e}")
                self.pdf_client = None
    
    def extract_from_base64(
        self, 
        content_bytes: str, 
        filename: str,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract data from a Base64-encoded PDF.
        
        Args:
            content_bytes: Base64-encoded PDF content
            filename: Original filename for temp file
            instructions: Optional custom extraction instructions
            
        Returns:
            Extracted data as dictionary
        """
        if not self.pdf_client:
            logger.error("PDF client not available")
            return {"error": "pdf_client_unavailable"}
        
        try:
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                pdf_bytes = base64.b64decode(content_bytes)
                tmp.write(pdf_bytes)
                tmp_path = tmp.name
            
            logger.info(f"📄 Processing PDF: {filename} ({len(pdf_bytes)} bytes)")
            
            # Extract using PDF client
            result = self.pdf_client.extract_items_from_pdf(
                pdf_path=tmp_path,
                instructions=instructions
            )
            
            # Cleanup temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
            
            if result:
                logger.info(f"✅ PDF extraction successful")
                return result
            else:
                logger.warning("PDF extraction returned None")
                return {"error": "extraction_failed", "filename": filename}
                
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return {"error": str(e), "filename": filename}
    
    def extract_from_file(
        self, 
        file_path: str,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract data from a PDF file path.
        
        Args:
            file_path: Path to PDF file
            instructions: Optional custom extraction instructions
            
        Returns:
            Extracted data as dictionary
        """
        if not self.pdf_client:
            logger.error("PDF client not available")
            return {"error": "pdf_client_unavailable"}
        
        if not os.path.exists(file_path):
            logger.error(f"PDF file not found: {file_path}")
            return {"error": "file_not_found", "path": file_path}
        
        try:
            logger.info(f"📄 Processing PDF: {file_path}")
            
            result = self.pdf_client.extract_items_from_pdf(
                pdf_path=file_path,
                instructions=instructions
            )
            
            if result:
                logger.info(f"✅ PDF extraction successful")
                return result
            else:
                return {"error": "extraction_failed", "path": file_path}
                
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return {"error": str(e), "path": file_path}
    
    def extract_project_info(
        self, 
        content_bytes: str, 
        filename: str
    ) -> Dict[str, Any]:
        """
        Extract project-relevant information from PDF.
        Uses a custom prompt for project extraction rather than invoice extraction.
        
        Args:
            content_bytes: Base64-encoded PDF content
            filename: Original filename
            
        Returns:
            Project-relevant extracted data
        """
        instructions = """
Analyze this PDF document and extract project-relevant information.

Return JSON with:
{
    "document_type": "invoice" | "specification" | "template" | "other",
    "client_hints": "Any company names or client references found",
    "data_fields": ["List of data fields/columns found"],
    "format_type": "Excel-like table" | "Form" | "Free text" | "Mixed",
    "layout_quality": "Native PDF" | "Scanned Image" | "Handwritten",
    "complexity": "simple" | "medium" | "complex",
    "notes": "Any relevant observations for project planning"
}

Return ONLY valid JSON.
"""
        return self.extract_from_base64(content_bytes, filename, instructions)
    
    def process_multiple(
        self, 
        attachments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process multiple PDF attachments.
        
        Args:
            attachments: List of attachment dicts with 'name' and 'content_bytes'
            
        Returns:
            List of extraction results
        """
        results = []
        
        for att in attachments:
            if att.get('content_bytes') and att.get('name', '').lower().endswith('.pdf'):
                result = self.extract_project_info(
                    att['content_bytes'],
                    att['name']
                )
                result['filename'] = att['name']
                results.append(result)
        
        return results
