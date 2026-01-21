import logging
import json
from typing import Optional, Dict, Any, List
from enum import Enum

# Internal Imports
from DonnaMemory.memory_service import MemoryService
from Donna.schema.email_payload import EmailPayload
from Donna.schema.project_context import ProjectContext, ExtractedData
from Donna.schema.odoo_fields import ProjectType, DataSource, Priority

# AI Components moved to Donna folder
from Donna.triage.attachment_analyzer import AttachmentAnalyzer, ProcessingStrategy
from Donna.triage.classifier import ProjectClassifier
from Donna.ai.text_processor import TextProcessor

logger = logging.getLogger(__name__)

class DonnaAction(Enum):
    CREATE_TASK = "CREATE_TASK"
    UPDATE_TASK = "UPDATE_TASK"
    MOVE_STAGE = "MOVE_STAGE"
    ADD_COMMENT = "ADD_COMMENT"
    IGNORE = "IGNORE"

class DonnaConductor:
    """
    The High-Level Conductor.
    Takes decisions based on memory and project state.
    """
    
    def __init__(self):
        self.memory = MemoryService()
        self.analyzer = AttachmentAnalyzer()
        self.classifier = ProjectClassifier()
        self.text_processor = TextProcessor()
        
    def orchestrate(self, email: EmailPayload) -> Dict[str, Any]:
        """
        The main intelligence loop.
        """
        logger.info(f"🧠 Donna Conductor: Orchestrating for {email.subject}")
        
        # 1. ANALYZE (Thinking Phase)
        strategy = self.analyzer.analyze(email)
        enriched_text = email.get_enriched_text()
        
        # 2. EXTRACT (What is this about?)
        extracted_data_dict = self.text_processor.extract(enriched_text)
        extracted_data = ExtractedData.from_dict(extracted_data_dict)
        
        # 3. MEMORY CHECK (Awareness Phase)
        # Search for semantically similar historical projects
        search_query = f"Task: {extracted_data.suggested_task_name or email.subject}\nClient: {extracted_data.client}\nDescription: {extracted_data.flow_type}"
        memory_match = self.memory.find_duplicate(search_query, threshold=0.7) # Lowered threshold slightly for better recall
        
        if memory_match:
            match_id = memory_match['id']
            score = memory_match['score']
            logger.info(f"💡 Memory Hit! Found existing context: {match_id} (Score: {score})")
            
            # DECISION: If it's a very strong match and involves a "next phase" or "update"
            # we should update/comment instead of create
            if "next phase" in email.body.lower() or "update" in email.body.lower():
                return {
                    "action": DonnaAction.MOVE_STAGE.value,
                    "target_task_id": int(match_id.split('_')[-1]),
                    "new_stage": "In Progress", # Logic for stage mapping
                    "context": extracted_data_dict,
                    "reason": f"Semantic match found ({match_id}) and user asked for next phase."
                }
            
            return {
                "action": DonnaAction.UPDATE_TASK.value,
                "target_task_id": int(match_id.split('_')[-1]),
                "context": extracted_data_dict,
                "reason": f"Semantic duplicate detected (Score: {score})."
            }

        # 4. NEW PROJECT (Classification Phase)
        project_type = self.classifier.classify(email, extracted_data)
        
        return {
            "action": DonnaAction.CREATE_TASK.value,
            "project_type": project_type.value,
            "context": extracted_data_dict,
            "reason": "No existing project found in memory."
        }
