"""
Donna AI Module
LLM integrations for text and PDF processing.
"""
from .prompt_router import PromptRouter
from .text_processor import TextProcessor
from .pdf_processor import PdfProcessor
from .prompts import (
    PROMPTS,
    TRIAGE_CLASSIFIER,
    INTERFACE_EXTRACTOR,
    AUTOMATION_EXTRACTOR,
    EMAIL_TO_FLOW,
    get_prompt
)

__all__ = [
    "PromptRouter", 
    "TextProcessor", 
    "PdfProcessor",
    "PROMPTS",
    "TRIAGE_CLASSIFIER",
    "INTERFACE_EXTRACTOR", 
    "AUTOMATION_EXTRACTOR",
    "EMAIL_TO_FLOW",
    "get_prompt"
]
