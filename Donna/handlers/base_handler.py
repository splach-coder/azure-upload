"""
Donna Handlers - Base Handler
Abstract base class for project handlers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from dataclasses import dataclass

from ..schema.project_context import ProjectContext


@dataclass
class OdooResult:
    """Result of an Odoo operation."""
    success: bool
    task_id: int = 0
    project_id: int = 0
    project_name: str = ""
    task_name: str = ""
    error: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "success": self.success,
            "task_id": self.task_id,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "task_name": self.task_name,
            "error": self.error if not self.success else None
        }


class BaseHandler(ABC):
    """
    Abstract base class for project handlers.
    
    Each handler is responsible for:
    1. Processing a specific project type
    2. Determining appropriate tags
    3. Creating the Odoo task
    """
    
    @abstractmethod
    def handle(self, context: ProjectContext) -> OdooResult:
        """
        Handle the project context and create Odoo task.
        
        Args:
            context: Complete project context from the Brain
            
        Returns:
            OdooResult with success status and task details
        """
        pass
    
    @abstractmethod
    def get_default_tags(self, context: ProjectContext) -> list:
        """
        Get default tags for this handler type.
        
        Args:
            context: Project context
            
        Returns:
            List of tag names
        """
        pass
    
    @abstractmethod
    def get_project_name(self, context: ProjectContext) -> str:
        """
        Get the Odoo project name for this handler.
        
        Args:
            context: Project context
            
        Returns:
            Project name string
        """
        pass
