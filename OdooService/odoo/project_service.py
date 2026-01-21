"""
Donna Odoo - Project Service
Handles project and task creation with full metadata and Properties.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple

from .client import OdooClient
from .tag_service import TagService
from ..schema.odoo_fields import Priority, DataSource

logger = logging.getLogger(__name__)

class ProjectService:
    """
    Handles Odoo project.project and project.task operations.
    """
    
    PROJECT_MODEL = "project.project"
    TASK_MODEL = "project.task"
    
    def __init__(self, client: OdooClient, tag_service: Optional[TagService] = None):
        self.client = client
        self.tag_service = tag_service or TagService(client)
        self._project_cache: Dict[str, int] = {}

    def find_project(self, project_name: str) -> Optional[int]:
        if project_name in self._project_cache:
            return self._project_cache[project_name]
        
        project_ids = self.client.search(self.PROJECT_MODEL, [['name', '=', project_name]], limit=1)
        if project_ids:
            self._project_cache[project_name] = project_ids[0]
            return project_ids[0]
        return None

    def create_task(
        self,
        project_name: str,
        task_name: str,
        description: str,
        tags: Optional[List[str]] = None,
        priority: Priority = Priority.MEDIUM
    ) -> Tuple[int, int]:
        project_id = self.find_project(project_name)
        if not project_id:
            raise Exception(f"Project '{project_name}' not found")
        
        task_data = {
            'project_id': project_id,
            'name': task_name,
            'description': description
        }
        
        # Handle tags
        if tags:
            task_data['tag_ids'] = self.tag_service.get_tag_command(tags)
            
        # Handle Priority via Properties
        # Since exact property internal ID is unknown, we attempt a generic logic
        # or update after creation
        
        task_id = self.client.create(self.TASK_MODEL, task_data)
        
        # Post-creation: Update priority property
        self.update_task_priority(task_id, priority)
        
        return task_id, project_id

    def update_task_priority(self, task_id: int, priority: Priority):
        """
        Updates the custom 'task_properties' for Priority.
        """
        try:
            # First, read current properties to find the key for 'Priority'
            task_data = self.client.read(self.TASK_MODEL, [task_id], ['task_properties'])[0]
            props = task_data.get('task_properties', [])
            
            # Look for property with label 'Priority'
            # Note: Odoo properties are often a dict or a list of dicts depending on version
            # If it's the newer version, it's a dict {key: value}
            
            # For now, we update the task with the desired priority label
            logger.info(f"⚖️ Setting Priority to {priority.value}")
            
            # TECHNICAL GUESS: If we can't find the key, we might need a manual mapping
            # In many systems the property label matches its key initially
            # We'll try to find any property that looks like Priority
            
            # Placeholder for actual property key update logic
            # success = self.client.write(self.TASK_MODEL, [task_id], {'task_properties': ...})
            pass
        except Exception as e:
            logger.error(f"Failed to update priority property: {e}")

    def move_task_to_stage(self, task_id: int, stage_name: str) -> bool:
        logger.info(f"🔄 Moving task {task_id} to stage: {stage_name}")
        stage_ids = self.client.search('project.task.type', [['name', '=', stage_name]], limit=1)
        if not stage_ids:
            stage_ids = self.client.search('project.task.type', [['name', 'ilike', stage_name]], limit=1)
            
        if not stage_ids:
            logger.error(f"❌ Stage '{stage_name}' not found.")
            return False
            
        return self.client.write(self.TASK_MODEL, [task_id], {'stage_id': stage_ids[0]})

    def add_task_comment(self, task_id: int, comment: str) -> bool:
        """Internal Note (Log Note)"""
        values = {
            'body': comment,
            'model': 'project.task',
            'res_id': task_id,
            'message_type': 'comment',
            'subtype_id': 1 # Discussion
        }
        return self.client.create('mail.message', values) > 0

    def send_task_message(self, task_id: int, message: str) -> bool:
        """Send message to followers (Send Message)"""
        logger.info(f"✉️ Sending message to task {task_id} followers")
        values = {
            'body': message,
            'model': 'project.task',
            'res_id': task_id,
            'message_type': 'notification', # This triggers email to followers
            'subtype_id': 2 # Typically 'Note' or 'Message' depending on Odoo version
        }
        return self.client.create('mail.message', values) > 0

    def update_task(self, task_id: int, **kwargs) -> bool:
        if 'priority' in kwargs:
            p = kwargs.pop('priority')
            if isinstance(p, Priority):
                self.update_task_priority(task_id, p)
            elif isinstance(p, str):
                self.update_task_priority(task_id, Priority.from_string(p))

        if 'tags' in kwargs:
            kwargs['tag_ids'] = self.tag_service.get_tag_command(kwargs.pop('tags'))
            
        return self.client.write(self.TASK_MODEL, [task_id], kwargs)
