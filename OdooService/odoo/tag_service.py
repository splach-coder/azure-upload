"""
Donna Odoo - Tag Service
Manages Odoo project tags (create, find, assign).
"""
import logging
from typing import List, Optional, Dict, Any

from .client import OdooClient

logger = logging.getLogger(__name__)


class TagService:
    """
    Handles Odoo project.tags operations.
    
    Provides:
    - Find or create tags by name
    - Get tag IDs for a list of names
    - Cache for performance
    """
    
    # Tag model name in Odoo
    TAG_MODEL = "project.tags"
    
    def __init__(self, client: OdooClient):
        """
        Initialize tag service.
        
        Args:
            client: Authenticated OdooClient
        """
        self.client = client
        self._tag_cache: Dict[str, int] = {}
    
    def find_or_create(self, tag_name: str) -> int:
        """
        Find a tag by name, or create it if it doesn't exist.
        
        Args:
            tag_name: Tag name to find/create
            
        Returns:
            Tag ID
        """
        # Check cache first
        if tag_name in self._tag_cache:
            logger.debug(f"🏷️ Tag from cache: {tag_name} -> {self._tag_cache[tag_name]}")
            return self._tag_cache[tag_name]
        
        # Search in Odoo
        tag_ids = self.client.search(self.TAG_MODEL, [['name', '=', tag_name]], limit=1)
        
        if tag_ids:
            tag_id = tag_ids[0]
            logger.info(f"🏷️ Found existing tag: {tag_name} (ID: {tag_id})")
        else:
            # Create new tag
            tag_id = self.client.create(self.TAG_MODEL, {'name': tag_name})
            logger.info(f"🏷️ Created new tag: {tag_name} (ID: {tag_id})")
        
        # Cache it
        self._tag_cache[tag_name] = tag_id
        
        return tag_id
    
    def get_tag_ids(self, tag_names: List[str]) -> List[int]:
        """
        Get tag IDs for a list of tag names.
        Creates any missing tags.
        
        Args:
            tag_names: List of tag names
            
        Returns:
            List of tag IDs
        """
        if not tag_names:
            return []
        
        tag_ids = []
        for name in tag_names:
            if name:  # Skip empty names
                tag_id = self.find_or_create(name)
                tag_ids.append(tag_id)
        
        return tag_ids
    
    def get_tag_command(self, tag_names: List[str]) -> List:
        """
        Get Odoo Many2many command for setting tags.
        
        Args:
            tag_names: List of tag names
            
        Returns:
            Odoo command: [(6, 0, [tag_ids])]
        """
        tag_ids = self.get_tag_ids(tag_names)
        return [(6, 0, tag_ids)]
    
    def add_tags_to_record(
        self, 
        model: str, 
        record_id: int, 
        tag_names: List[str],
        tag_field: str = "tag_ids"
    ) -> bool:
        """
        Add tags to an existing record.
        
        Args:
            model: Odoo model (e.g., 'project.task')
            record_id: Record ID to update
            tag_names: List of tag names to add
            tag_field: Field name for tags (default: 'tag_ids')
            
        Returns:
            True if successful
        """
        tag_ids = self.get_tag_ids(tag_names)
        
        if not tag_ids:
            logger.warning("No tags to add")
            return True
        
        # Use command (4, id, 0) to add each tag without replacing existing
        commands = [(4, tag_id, 0) for tag_id in tag_ids]
        
        return self.client.write(model, [record_id], {tag_field: commands})
    
    def list_all_tags(self) -> List[Dict[str, Any]]:
        """
        List all available tags.
        
        Returns:
            List of tag records with 'id' and 'name'
        """
        return self.client.search_read(
            self.TAG_MODEL, 
            [], 
            fields=['id', 'name', 'color']
        )
    
    def clear_cache(self):
        """Clear the tag cache."""
        self._tag_cache.clear()
        logger.info("Tag cache cleared")
    
    def preload_cache(self):
        """Preload all tags into cache for performance."""
        all_tags = self.list_all_tags()
        for tag in all_tags:
            self._tag_cache[tag['name']] = tag['id']
        logger.info(f"Preloaded {len(all_tags)} tags into cache")
