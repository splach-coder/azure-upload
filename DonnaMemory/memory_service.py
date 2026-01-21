import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pinecone import Pinecone

from DonnaMemory.config import Config

logger = logging.getLogger(__name__)

class MemoryService:
    """
    Manages Donna's Long-Term Memory (Pinecone Vector DB).
    Adheres to the Multi-Resource Memory Contract.
    """
    
    def __init__(self):
        """Initialize Pinecone client."""
        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.index_name = Config.INDEX_NAME
        self.index = None
    
    def _ensure_index(self):
        """Ensure the index exists and is configured correctly."""
        try:
            if not self.pc.has_index(self.index_name):
                logger.info(f"🧠 Creating new memory index: {self.index_name}")
                self.pc.create_index_for_model(
                    name=self.index_name,
                    cloud=Config.PINECONE_CLOUD,
                    region=Config.PINECONE_ENV,
                    embed={
                        "model": "llama-text-embed-v2",
                        "field_map": {"text": "chunk_text"}
                    }
                )
            
            # Get the index instance
            self.index = self.pc.Index(self.index_name)
            
        except Exception as e:
            logger.error(f"Failed to ensure index: {e}")
            raise
    
    def enrich_from_odoo(self, project_context: Dict[str, Any], task_id: int):
        """
        Store Odoo Project Context in Memory.
        
        Args:
            project_context: The full context dictionary from Donna
            task_id: The created Odoo Task ID
        """
        self._ensure_index()
        
        # 1. Prepare Metadata (The Contract)
        description = project_context.get('task_description', '') or project_context.get('description', '')
        client = project_context.get('extracted_data', {}).get('client', 'Unknown')
        
        # Create a rich text representation for embedding
        searchable_text = f"""
        Project: {project_context.get('task_name')}
        Client: {client}
        Type: {project_context.get('project_type', 'Unknown')}
        Tags: {','.join(project_context.get('tags', []))}
        
        Description:
        {description}
        """
        
        # 2. Structure the Record (Flat structure for upsert_records)
        record = {
            "_id": f"odoo_task_{task_id}",
            "chunk_text": searchable_text.strip(),
            "resource_type": "odoo_project",
            "origin_id": str(task_id),
            "client_tag": client,
            "category": project_context.get('project_type', 'INTERFACE'),
            "created_at": datetime.utcnow().isoformat()
        }
        
        # 3. Upsert
        logger.info(f"🧠 Memorizing Odoo Task {task_id} for {client}")
        # When using integrated inference, use upsert_records with flat records
        self.index.upsert_records(namespace="__default__", records=[record])
        logger.info(f"✅ Memory stored successfully")

    def search(self, query: str, filters: Optional[Dict] = None, top_k: int = 3):
        """Search memory with integrated inference."""
        self._ensure_index()
        # Pinecone 8.0.0 Integrated Inference uses 'inputs' field
        search_query = {
            "inputs": {"text": query}, 
            "top_k": top_k
        }
        if filters:
            search_query["filter"] = filters
            
        return self.index.search(namespace="__default__", query=search_query)

    def find_duplicate(self, text: str, resource_type: Optional[str] = None, threshold: float = 0.85) -> Optional[Dict[str, Any]]:
        """
        Find the most similar record in memory.
        Returns the match if score > threshold.
        """
        self._ensure_index()
        
        # Build query with 'inputs' and filter if provided
        search_query = {
            "inputs": {"text": text},
            "top_k": 1
        }
        if resource_type:
            search_query["filter"] = {"resource_type": {"$eq": resource_type}}
            
        logger.info(f"🔍 Checking memory for duplicate")
        results = self.index.search(namespace="__default__", query=search_query)
        
        if results.hits:
            best_match = results.hits[0]
            if best_match.score >= threshold:
                logger.info(f"🎯 Found semantic match: {best_match.id} (Score: {best_match.score})")
                return {
                    "id": str(best_match.id),
                    "score": float(best_match.score),
                    "metadata": dict(best_match.metadata) if best_match.metadata else {}
                }
        
        return None
