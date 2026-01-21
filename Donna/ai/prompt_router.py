"""
Donna AI - Prompt Router
Selects appropriate prompts based on processing context.
"""
import logging
from typing import Dict

from .prompts import PROMPTS, get_prompt

logger = logging.getLogger(__name__)


class PromptRouter:
    """
    Routes to the correct prompt based on processing context.
    
    Available prompts:
    - classify: Classifies project type (INTERFACE vs AUTOMATION)
    - interface: Extracts interface project details
    - automation: Extracts automation project details
    - email_to_flow: General email parsing
    """
    
    def __init__(self):
        """Initialize prompt router."""
        self._prompt_cache: Dict[str, str] = {}
    
    def get_prompt(self, purpose: str) -> str:
        """
        Get prompt content for a specific purpose.
        
        Args:
            purpose: One of 'classify', 'interface', 'automation', 'email_to_flow'
            
        Returns:
            Prompt text content
            
        Raises:
            ValueError: If purpose is unknown
        """
        # Check cache
        if purpose in self._prompt_cache:
            return self._prompt_cache[purpose]
        
        # Get from prompts module
        prompt = get_prompt(purpose)
        
        # Cache it
        self._prompt_cache[purpose] = prompt
        logger.info(f"📝 Loaded prompt: {purpose}")
        
        return prompt
    
    def clear_cache(self):
        """Clear the prompt cache."""
        self._prompt_cache.clear()
        logger.info("Prompt cache cleared")
    
    def list_available_prompts(self) -> Dict[str, str]:
        """List all available prompts."""
        return {purpose: f"{len(content)} chars" for purpose, content in PROMPTS.items()}
