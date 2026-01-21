import logging
import requests
import json
from typing import Dict, Any, Optional

from ..config import Config

logger = logging.getLogger(__name__)

class MemoryConnector:
    """
    Connects StoreProjectOnOdoo to the DonnaMemory microservice.
    This ensures Donna is a 'Self-Learner' by archiving every 
    created project in her vector memory.
    """
    
    @staticmethod
    def archive_task(context: Any, task_id: int):
        """
        Sends the project context to the Memory Service.
        
        Args:
            context: The ProjectContext object
            task_id: The Odoo Task ID
        """
        try:
            # 1. Prepare payload
            # We convert context to dict if it's an object
            context_dict = context.to_dict() if hasattr(context, 'to_dict') else str(context)
            
            payload = {
                "action": "enrich_odoo",
                "task_id": task_id,
                "context": context_dict
            }
            
            # 2. Try to use the shared MemoryService logic if possible (for performance)
            # Otherwise fallback to HTTP
            try:
                from DonnaMemory.memory_service import MemoryService
                service = MemoryService()
                service.enrich_from_odoo(context_dict, task_id)
                logger.info(f"🧠 Task {task_id} successfully memorized via internal service.")
                return True
            except ImportError:
                # Fallback to HTTP call if the module is not accessible
                logger.warning("DonnaMemory module not found. Falling back to HTTP.")
                response = requests.post(
                    Config.MEMORY_SERVICE_URL,
                    json=payload,
                    timeout=10
                )
                if response.status_code == 200:
                    logger.info(f"🧠 Task {task_id} successfully memorized via HTTP.")
                    return True
                else:
                    logger.error(f"❌ Failed to memorize task: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"⚠️ Memory Archiving Error: {e}")
            return False
