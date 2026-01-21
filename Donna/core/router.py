"""
Donna Core - Router
Routes to appropriate handlers based on project type.
"""
import logging
from typing import Dict, Type, Optional

from ..schema.odoo_fields import ProjectType
from ..handlers.base_handler import BaseHandler
from ..handlers.interface_handler import InterfaceHandler
from ..handlers.automation_handler import AutomationHandler

logger = logging.getLogger(__name__)


class Router:
    """
    Routes requests to the appropriate handler based on project type.
    
    Supports:
    - INTERFACE -> InterfaceHandler
    - AUTOMATION -> AutomationHandler
    - UNKNOWN -> InterfaceHandler (fallback)
    """
    
    # Handler mapping
    HANDLERS: Dict[ProjectType, Type[BaseHandler]] = {
        ProjectType.INTERFACE: InterfaceHandler,
        ProjectType.AUTOMATION: AutomationHandler,
        ProjectType.UNKNOWN: InterfaceHandler,  # Fallback
    }
    
    def __init__(self):
        """Initialize router with handler instances."""
        self._handler_cache: Dict[ProjectType, BaseHandler] = {}
    
    def get_handler(self, project_type: ProjectType) -> BaseHandler:
        """
        Get the appropriate handler for the project type.
        
        Args:
            project_type: The classified project type
            
        Returns:
            Handler instance
        """
        # Check cache
        if project_type in self._handler_cache:
            return self._handler_cache[project_type]
        
        # Get handler class
        handler_class = self.HANDLERS.get(project_type)
        
        if not handler_class:
            logger.warning(f"No handler for {project_type}, using InterfaceHandler")
            handler_class = InterfaceHandler
        
        # Instantiate and cache
        handler = handler_class()
        self._handler_cache[project_type] = handler
        
        logger.info(f"🚦 Routed to {handler_class.__name__}")
        return handler
    
    def register_handler(
        self, 
        project_type: ProjectType, 
        handler_class: Type[BaseHandler]
    ):
        """
        Register a custom handler for a project type.
        
        Args:
            project_type: Project type to handle
            handler_class: Handler class (not instance)
        """
        self.HANDLERS[project_type] = handler_class
        # Clear cache for this type
        if project_type in self._handler_cache:
            del self._handler_cache[project_type]
        
        logger.info(f"Registered {handler_class.__name__} for {project_type}")
    
    def clear_cache(self):
        """Clear handler cache (useful for testing)."""
        self._handler_cache.clear()
