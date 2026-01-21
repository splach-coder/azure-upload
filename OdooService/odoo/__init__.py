"""
Donna Odoo Module
Odoo integration for projects, tasks, tags, and attachments.
"""
from .client import OdooClient
from .tag_service import TagService
from .project_service import ProjectService

__all__ = ["OdooClient", "TagService", "ProjectService"]
