"""
Donna AI - Text Processor
Wrapper for CustomCall to process text-only emails.
"""
import json
import logging
import os
import sys
from typing import Dict, Any, Optional

from .prompt_router import PromptRouter

logger = logging.getLogger(__name__)


class TextProcessor:
    """
    Processes text-only emails using CustomCall (OpenAI).
    
    Used when:
    - Email has no attachments
    - Attachments are not PDF/Excel
    - Fallback for other processing failures
    """
    
    def __init__(self, llm_client=None, prompt_router: Optional[PromptRouter] = None):
        """
        Initialize text processor.
        
        Args:
            llm_client: Optional LLM client (CustomCall)
            prompt_router: Optional prompt router
        """
        self.llm = llm_client
        self.prompt_router = prompt_router or PromptRouter()
        self._init_llm()
    
    def _init_llm(self):
        """Initialize LLM client if not provided."""
        if self.llm is None:
            try:
                from ..openai_api import CustomCall
                self.llm = CustomCall()
                logger.info("✅ TextProcessor LLM initialized")
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {e}")
                self.llm = None
    
    def extract(self, email_text: str, prompt_purpose: str = "email_to_flow") -> Dict[str, Any]:
        """
        Extract structured data from email text.
        
        Args:
            email_text: The enriched email text
            prompt_purpose: Which prompt to use ('email_to_flow', 'interface', 'automation')
            
        Returns:
            Extracted data as dictionary
        """
        if not self.llm:
            logger.error("LLM not available")
            return self._fallback_extraction(email_text)
        
        try:
            # Get appropriate prompt
            prompt = self.prompt_router.get_prompt(prompt_purpose)
            
            logger.info(f"📝 Using prompt: {prompt_purpose}")
            logger.info(f"📧 Processing text ({len(email_text)} chars)")
            
            # Call LLM
            response = self.llm.send_request(prompt, email_text)
            
            if not response:
                logger.warning("Empty LLM response, using fallback")
                return self._fallback_extraction(email_text)
            
            logger.info(f"🤖 LLM Response: {response[:200]}...")
            
            # Parse JSON response
            return self._parse_response(response)
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return self._fallback_extraction(email_text)
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response as JSON."""
        # Clean potential markdown
        cleaned = response.replace("```json", "").replace("```", "").strip()
        
        try:
            data = json.loads(cleaned)
            logger.info(f"✅ Parsed response: {list(data.keys())}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Raw response: {cleaned[:500]}")
            return {"error": "parse_failed", "raw": cleaned}
    
    def _fallback_extraction(self, email_text: str) -> Dict[str, Any]:
        """
        Fallback extraction when LLM is unavailable.
        Uses simple heuristics.
        """
        logger.info("🔄 Using fallback extraction")
        
        lines = email_text.split('\n')
        result = {
            "client": "Unknown",
            "flow_type": "Unknown",
            "source": "Email",
            "subject_used": True,
            "attachments": [],
            "output_format": "Excel"
        }
        
        # Try to extract basic info from structured email
        for line in lines:
            if line.startswith("FROM:"):
                sender = line.replace("FROM:", "").strip()
                # Try to extract company from email domain
                if "@" in sender:
                    domain = sender.split("@")[1].split(".")[0]
                    result["client"] = domain.title()
            elif line.startswith("SUBJECT:"):
                subject = line.replace("SUBJECT:", "").strip()
                result["flow_type"] = subject[:50] if subject else "Unknown"
            elif line.startswith("ATTACHMENT TYPES:"):
                types = line.replace("ATTACHMENT TYPES:", "").strip()
                if types and types != "None":
                    result["attachments"] = [t.strip() for t in types.split(",")]
        
        return result
