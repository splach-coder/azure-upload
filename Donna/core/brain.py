"""
Donna Core - Brain
The central decision engine that orchestrates all processing.
"""
import logging
from typing import Optional, Dict, Any

from ..schema.email_payload import EmailPayload
from ..schema.project_context import ProjectContext, ExtractedData
from ..schema.odoo_fields import ProjectType, DataSource, Priority
from ..triage.attachment_analyzer import AttachmentAnalyzer, ProcessingStrategy
from ..triage.classifier import ProjectClassifier
from ..ai.text_processor import TextProcessor
from ..ai.pdf_processor import PdfProcessor
from ..handlers.base_handler import BaseHandler, OdooResult
from .router import Router

logger = logging.getLogger(__name__)


class DonnaBrain:
    """
    Central decision engine - THE brain of Donna.
    
    Responsibilities:
    1. Receive email payload from Azure Function
    2. Analyze: Does it have attachments?
    3. Route to appropriate processor (text-only vs PDF/Excel)
    4. Classify project type (INTERFACE vs AUTOMATION)
    5. Build complete project context
    6. Delegate to the correct handler
    
    Flow:
    ┌─────────────┐
    │ EmailPayload │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ Attachment  │
    │  Analyzer   │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ AI Processor │─── TextProcessor or PdfProcessor
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ Classifier  │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ Handler     │─── InterfaceHandler or AutomationHandler
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ OdooResult  │
    └─────────────┘
    """
    
    def __init__(
        self,
        attachment_analyzer: Optional[AttachmentAnalyzer] = None,
        classifier: Optional[ProjectClassifier] = None,
        text_processor: Optional[TextProcessor] = None,
        pdf_processor: Optional[PdfProcessor] = None,
        router: Optional[Router] = None
    ):
        """
        Initialize the brain with all components.
        
        Args:
            attachment_analyzer: Optional custom analyzer
            classifier: Optional custom classifier
            text_processor: Optional custom text processor
            pdf_processor: Optional custom PDF processor
            router: Optional custom router
        """
        self.attachment_analyzer = attachment_analyzer or AttachmentAnalyzer()
        self.classifier = classifier or ProjectClassifier()
        self.text_processor = text_processor or TextProcessor()
        self.pdf_processor = pdf_processor or PdfProcessor()
        self.router = router or Router()
        
        logger.info("🧠 Donna Brain initialized")
    
    def process(self, email: EmailPayload) -> ProjectContext:
        """
        Process an email and build complete project context.
        
        This is the THINKING phase - no Odoo operations yet.
        
        Args:
            email: Parsed email payload
            
        Returns:
            Complete ProjectContext ready for handler
        """
        logger.info("🧠 Donna is thinking...")
        logger.info(f"📧 Processing email from: {email.from_address}")
        logger.info(f"📋 Subject: {email.subject}")
        
        # Step 1: Analyze attachments to determine processing strategy
        strategy = self.attachment_analyzer.analyze(email)
        logger.info(f"📊 Processing strategy: {strategy.value}")
        
        # Step 2: Extract information using appropriate AI processor
        extracted_data = self._extract_data(email, strategy)
        logger.info(f"✅ Extracted: client={extracted_data.client}, flow_type={extracted_data.flow_type}")
        
        # Step 3: Classify project type
        project_type = self.classifier.classify(email, extracted_data)
        logger.info(f"🎯 Classification: {project_type.value}")
        
        # Step 4: Determine tags
        tags = self._determine_tags(email, extracted_data, project_type)
        logger.info(f"🏷️ Tags: {tags}")
        
        # Step 5: Determine data sources
        data_sources = self._determine_data_sources(email)
        logger.info(f"📊 Data sources: {[ds.value for ds in data_sources]}")
        
        # Step 6: Determine priority
        priority = Priority.from_importance(email.importance)
        logger.info(f"⚡ Priority: {priority.value}")
        
        # Build complete context
        context = ProjectContext(
            email=email,
            extracted_data=extracted_data,
            project_type=project_type,
            tags=tags,
            data_sources=data_sources,
            priority=priority
        )
        
        logger.info(f"🧠 Donna finished thinking. Task: '{context.task_name}'")
        return context
    
    def _extract_data(
        self, 
        email: EmailPayload, 
        strategy: ProcessingStrategy
    ) -> ExtractedData:
        """
        Extract data using the appropriate AI processor.
        
        Args:
            email: Email payload
            strategy: Processing strategy from analyzer
            
        Returns:
            Extracted data
        """
        # Get base enriched text
        enriched_text = email.get_enriched_text()
        
        pdf_analysis_summary = ""
        pdf_results = []
        
        # Process PDFs if needed
        if strategy in [ProcessingStrategy.PDF, ProcessingStrategy.MIXED]:
            pdf_results = self._process_pdfs(email)
            if pdf_results:
                # Build summary from PDF results
                summaries = []
                for res in pdf_results:
                    fname = res.get('filename', 'unknown')
                    layout = res.get('layout_quality', 'Unknown')
                    comp = res.get('complexity', 'unknown')
                    fmt = res.get('format_type', 'unknown')
                    summaries.append(f"- {fname}: {layout} quality, {fmt} format, {comp} complexity")
                
                pdf_analysis_summary = "\n\nPDF ANALYSIS:\n" + "\n".join(summaries)
        
        # Append PDF analysis to text context for better LLM decision making
        full_context = enriched_text + pdf_analysis_summary
        
        # Process Text (with full context)
        text_result = self.text_processor.extract(full_context)
        
        # Merge results if PDFs were processed
        if pdf_results:
            merged = {**text_result, 'pdf_analysis': pdf_results}
            return ExtractedData.from_dict(merged)
            
        return ExtractedData.from_dict(text_result)
    
    def _process_pdfs(self, email: EmailPayload) -> list:
        """Process PDF attachments."""
        results = []
        
        for att in email.attachments:
            if att.is_pdf and att.content_bytes:
                result = self.pdf_processor.extract_project_info(
                    att.content_bytes,
                    att.name
                )
                if result:
                    result['filename'] = att.name
                    results.append(result)
        
        return results
    
    def _determine_tags(
        self, 
        email: EmailPayload, 
        extracted: ExtractedData,
        project_type: ProjectType
    ) -> list:
        """
        Determine tags based on all available information.
        NOTE: Handlers now enforce strict tagging rules. 
        This method returns initial raw tags for context.
        """
        tags = []
        
        # Add project type tag
        tags.append(project_type.value)
        
        return tags
    
    def _determine_data_sources(self, email: EmailPayload) -> list:
        """
        Determine data sources from email.
        
        Args:
            email: Email payload
            
        Returns:
            List of DataSource enums
        """
        sources = [DataSource.EMAIL]  # Always from email
        
        if email.has_pdf:
            sources.append(DataSource.PDF)
        
        if email.has_excel:
            sources.append(DataSource.EXCEL)
        
        return sources
    
    def get_handler(self, project_type: ProjectType) -> BaseHandler:
        """
        Get the appropriate handler for the project type.
        
        Args:
            project_type: Classified project type
            
        Returns:
            Handler instance
        """
        return self.router.get_handler(project_type)
    
    def execute(self, context: ProjectContext) -> OdooResult:
        """
        Execute the project context - create Odoo task.
        
        This is the ACTION phase.
        
        Args:
            context: Complete project context
            
        Returns:
            OdooResult from handler
        """
        logger.info("🚀 Donna is executing...")
        
        # Get appropriate handler
        handler = self.get_handler(context.project_type)
        
        # Execute
        result = handler.handle(context)
        
        if result.success:
            logger.info(f"✅ Success! Task ID: {result.task_id} in '{result.project_name}'")
        else:
            logger.error(f"❌ Failed: {result.error}")
        
        return result
    
    def process_and_execute(self, email: EmailPayload) -> OdooResult:
        """
        Complete pipeline: process email and execute.
        
        Convenience method that combines process() and execute().
        
        Args:
            email: Raw email payload
            
        Returns:
            OdooResult
        """
        # Think
        context = self.process(email)
        
        # Act
        return self.execute(context)
