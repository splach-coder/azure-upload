"""
Donna Schema - Odoo Fields
Enum definitions matching Odoo project fields.
"""
from enum import Enum
from typing import List


class ProjectType(Enum):
    """
    Project type classification.
    Determines which handler processes the request.
    """
    INTERFACE = "INTERFACE"      # Logistics/data mapping projects
    AUTOMATION = "AUTOMATION"    # Process automation/scripting projects
    UNKNOWN = "UNKNOWN"          # Fallback for unclassified


class Tag(Enum):
    """
    Standard Odoo project tags.
    Client tags are created dynamically by AI detection.
    """
    INTERFACE = "INTERFACE"
    AUTOMATION = "AUTOMATION"
    URGENT = "Urgent"
    
    @classmethod
    def get_value(cls, name: str) -> str:
        """Get tag value by name, or return the name itself for dynamic tags."""
        try:
            return cls[name.upper().replace(' ', '_')].value
        except KeyError:
            return name  # Return as-is for dynamic client tags


class DataSource(Enum):
    """
    Data source types for Odoo tasks.
    Maps to x_data_sources or similar custom field.
    """
    EXCEL = "Excel"
    EMAIL = "Email"
    PDF = "PDF"
    API = "API"
    SFTP = "SFTP"
    
    @classmethod
    def from_attachment_types(cls, types: List[str]) -> List["DataSource"]:
        """Convert attachment type strings to DataSource enums."""
        mapping = {
            "PDF": cls.PDF,
            "Excel": cls.EXCEL,
            "Image": None,  # Images don't map to a data source
            "Other": None
        }
        sources = [mapping.get(t) for t in types if mapping.get(t)]
        sources.append(cls.EMAIL)  # Always include EMAIL as source
        return list(set(sources))


class Priority(Enum):
    """
    Task priority levels for Properties field.
    """
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    
    @classmethod
    def from_importance(cls, importance: str) -> "Priority":
        """Map email importance to priority."""
        mapping = {
            "low": cls.LOW,
            "normal": cls.MEDIUM,
            "high": cls.HIGH,
            "urgent": cls.HIGH
        }
        return mapping.get(importance.lower(), cls.MEDIUM)
    
    @classmethod
    def from_string(cls, value: str) -> "Priority":
        """Parse priority from string."""
        mapping = {
            "low": cls.LOW,
            "medium": cls.MEDIUM,
            "high": cls.HIGH,
            "normal": cls.MEDIUM,
            "critical": cls.HIGH
        }
        return mapping.get(value.lower(), cls.MEDIUM)


class OdooProject(Enum):
    """
    Known Odoo projects.
    """
    INTERFACE = "Interface"
    AUTOMATION = "Automation"
    
    @classmethod
    def from_project_type(cls, project_type: ProjectType) -> "OdooProject":
        """Map ProjectType to OdooProject."""
        mapping = {
            ProjectType.INTERFACE: cls.INTERFACE,
            ProjectType.AUTOMATION: cls.AUTOMATION,
            ProjectType.UNKNOWN: cls.INTERFACE  # Default fallback
        }
        return mapping.get(project_type, cls.INTERFACE)
