"""
Donna Handlers - Automation Handler
Handles AUTOMATION type projects (scripts, workflows, integrations).
"""
import logging
from typing import List, Optional

from .base_handler import BaseHandler, OdooResult
from ..schema.project_context import ProjectContext
from ..schema.odoo_fields import DataSource, Priority
from ..schema import format_automation_description, get_subtasks_for_type
from ..odoo.client import OdooClient
from ..odoo.project_service import ProjectService
from ..config import Config
from ..core.memory_connector import MemoryConnector

logger = logging.getLogger(__name__)


class AutomationHandler(BaseHandler):
    """
    Handles AUTOMATION type projects.
    
    These are typically:
    - Script development
    - Workflow automation
    - API integrations
    - Scheduled tasks
    - Logic App/Azure Function development
    
    Default Tags: AUTOMATION, [Client Name]
    Project: Automation (fallback to Interface if not exists)
    """
    
    def __init__(self, project_service: Optional[ProjectService] = None):
        """
        Initialize automation handler.
        
        Args:
            project_service: Optional ProjectService (will create if not provided)
        """
        self.project_service = project_service
        self._init_service()
    
    def _init_service(self):
        """Initialize Odoo service if not provided."""
        if self.project_service is None:
            try:
                client = OdooClient(
                    url=Config.ODOO_URL,
                    db=Config.ODOO_DB,
                    username=Config.ODOO_USERNAME,
                    api_key=Config.ODOO_API_KEY
                )
                self.project_service = ProjectService(client)
                logger.info("✅ AutomationHandler initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Odoo service: {e}")
                self.project_service = None
    
    def handle(self, context: ProjectContext) -> OdooResult:
        """
        Handle AUTOMATION project and create Odoo task.
        
        Args:
            context: Complete project context
            
        Returns:
            OdooResult with task creation details
        """
        if not self.project_service:
            return OdooResult(
                success=False,
                error="Odoo service not initialized"
            )
        
        try:
            # Get tags
            tags = self.get_default_tags(context)
            
            # Get data sources
            data_sources = self._get_data_sources(context)
            
            # Get project name
            project_name = self.get_project_name(context)
            
            # CHECK FOR DUPLICATES
            existing_task_id = self.project_service.find_duplicate_task(project_name, context.task_name)
            if existing_task_id:
                logger.warning(f"⚠️ Task '{context.task_name}' already exists (ID: {existing_task_id}). Skipping creation.")
                return OdooResult(
                    success=True,
                    task_id=existing_task_id,
                    project_id=0,
                    project_name=project_name,
                    task_name=context.task_name,
                    error="Duplicate task found - skipped creation"
                )
            
            # Create task
            logger.info(f"⚙️ AutomationHandler creating task in '{project_name}'")
            logger.info(f"   Tags: {tags}")
            logger.info(f"   Data Sources: {[ds.value for ds in data_sources]}")
            
            # Generate markdown description
            description = format_automation_description(
                client=context.extracted_data.client,
                flow_type=context.extracted_data.flow_type,
                summary=context.task_description,
                from_address=context.email.from_address,
                subject=context.email.subject,
                received_at=context.email.received_at, # Using property
                triggers=context.extracted_data.triggers,
                actions=context.extracted_data.actions,
                integrations=context.extracted_data.integrations,
                logic_app_name=context.extracted_data.logic_app,
                azure_function_name=context.extracted_data.azure_function,
                schedule=context.extracted_data.schedule,
                keywords=context.extracted_data.keywords
            )

            task_id, project_id = self.project_service.create_task(
                project_name=project_name,
                task_name=context.task_name,
                description=description,
                tags=tags,
                data_sources=data_sources,
                priority=context.priority
            )
            
            # Create subtasks
            subtasks = get_subtasks_for_type("AUTOMATION")
            self.project_service.create_subtasks(task_id, project_id, subtasks)
            
            # Upload attachments
            self.project_service.upload_task_attachments(task_id, context.email.attachments)
            
            # MEMORIZE (Self-Learning)
            MemoryConnector.archive_task(context, task_id)
            
            return OdooResult(
                success=True,
                task_id=task_id,
                project_id=project_id,
                project_name=project_name,
                task_name=context.task_name
            )
            
        except Exception as e:
            # If Automation project doesn't exist, try Interface as fallback
            if "not found" in str(e).lower():
                logger.warning("Automation project not found, falling back to Interface")
                try:
                    task_id, project_id = self.project_service.create_task(
                        project_name="Interface",
                        task_name=context.task_name,
                        description=context.task_description + "\n\n[Originally: AUTOMATION project]",
                        tags=tags,
                        data_sources=data_sources,
                        priority=context.priority
                    )
                    
                    # MEMORIZE (Self-Learning Fallback)
                    MemoryConnector.archive_task(context, task_id)
                    
                    return OdooResult(
                        success=True,
                        task_id=task_id,
                        project_id=project_id,
                        project_name="Interface",
                        task_name=context.task_name
                    )
                except Exception as e2:
                    logger.error(f"Fallback also failed: {e2}")
                    return OdooResult(success=False, error=str(e2))
            
            logger.error(f"AutomationHandler failed: {e}")
            return OdooResult(
                success=False,
                task_name=context.task_name,
                error=str(e)
            )
    
    def get_default_tags(self, context: ProjectContext) -> List[str]:
        """
        Get default tags for AUTOMATION projects.
        Strict Rules:
        1. Always include 'AUTOMATION'
        2. Check for subsidiary companies (Van Poppel, Vermaas)
        3. No client names or person names
        """
        tags = ["AUTOMATION"]
        
        # Check text for company identification
        full_text = f"{context.email.subject} {context.email.body} {context.email.from_address}".lower()
        
        is_subsidiary = False
        if "vanpoppel" in full_text or "van poppel" in full_text:
            tags.append("VanPoppel")
            is_subsidiary = True
        elif "vermaas" in full_text:
            tags.append("Vermaas")
            is_subsidiary = True
            
        # If no subsidiary detected, it implies DKM (Mother Company)
        if not is_subsidiary:
            tags.append("DKM")
        
        return list(set(tags))
    
    def get_project_name(self, context: ProjectContext) -> str:
        """
        Get project name for AUTOMATION projects.
        
        Returns:
            'Automation' if exists, else will fallback in handle()
        """
        return "Automation"
    
    def _get_data_sources(self, context: ProjectContext) -> List[DataSource]:
        """
        Determine data sources from context.
        Automation projects often involve API integrations.
        
        Args:
            context: Project context
            
        Returns:
            List of DataSource enums
        """
        data_sources = [DataSource.EMAIL]  # Always from email
        
        # Check for API mentions in email
        email_text = f"{context.email.subject} {context.email.body}".lower()
        if any(kw in email_text for kw in ['api', 'integration', 'endpoint', 'webhook']):
            data_sources.append(DataSource.API)
        
        if any(kw in email_text for kw in ['sftp', 'ftp', 'file transfer']):
            data_sources.append(DataSource.SFTP)
        
        # Add based on attachments
        if context.email.has_excel:
            data_sources.append(DataSource.EXCEL)
        
        if context.email.has_pdf:
            data_sources.append(DataSource.PDF)
        
        return data_sources
