"""
Donna Schema Module
Data models for email payloads, project context, and Odoo fields.
"""
from .email_payload import EmailPayload, Attachment
from .project_context import ProjectContext
from .odoo_fields import ProjectType, Tag, DataSource, Priority, OdooProject
from .description_formatter import (
    format_interface_description, 
    format_automation_description,
    get_subtasks_for_type,
    SubTask
)

__all__ = [
    "EmailPayload", 
    "Attachment", 
    "ProjectContext",
    "ProjectType", 
    "Tag", 
    "DataSource", 
    "Priority",
    "OdooProject",
    "format_interface_description",
    "format_automation_description",
    "get_subtasks_for_type",
    "SubTask"
]
