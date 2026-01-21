"""
Donna Conductor - Supreme AI Orchestrator
The single entry point that manages intelligence, memory, and workers.
"""
import azure.functions as func
import logging
import json
import requests
import sys
import os

# Add paths for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Donna.brain import DonnaConductor, DonnaAction
from OdooService.schema.email_payload import EmailPayload

logger = logging.getLogger(__name__)

# Config for internal microservice calls
ODOO_SERVICE_URL = "http://localhost:7071/api/OdooService"
MEMORY_SERVICE_URL = "http://localhost:7071/api/DonnaMemory"

async def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('👸 Donna: Orchestrating Request')
    
    try:
        body = req.get_json()
        email = EmailPayload.from_request(body)
        
        # 1. ORCHESTRATE (Think)
        conductor = DonnaConductor()
        decision = conductor.orchestrate(email)
        
        action = decision.get("action")
        logger.info(f"🎯 Decision: {action} - Reason: {decision.get('reason')}")

        # 2. EXECUTE (Act via Workers)
        result_data = {}
        
        if action == DonnaAction.CREATE_TASK.value:
            # Tell Odoo Worker to create
            odoo_req = {
                "command": "CREATE_TASK",
                "project_name": decision.get("project_type"),
                "task_name": decision.get("context", {}).get("task_name") or f"{decision.get('context', {}).get('client')} - {decision.get('context', {}).get('flow_type')}",
                "description": decision.get("context", {}).get("description", "Created by Donna")
            }
            resp = requests.post(ODOO_SERVICE_URL, json=odoo_req)
            result_data = resp.json()

        elif action == DonnaAction.MOVE_STAGE.value:
            # Tell Odoo Worker to move
            task_id = decision.get("target_task_id")
            stage = decision.get("new_stage")
            
            # 1. Move Stage
            requests.post(ODOO_SERVICE_URL, json={
                "command": "MOVE_STAGE",
                "task_id": task_id,
                "stage_name": stage
            })
            
            # 2. Add Comment explaining why
            comment = f"<b>Donna:</b> Automatically moved to '{stage}' based on email: \"{email.subject}\".<br/>Reason: {decision.get('reason')}"
            requests.post(ODOO_SERVICE_URL, json={
                "command": "ADD_COMMENT",
                "task_id": task_id,
                "comment": comment
            })
            
            result_data = {"success": True, "task_id": task_id, "action": "MOVED_STAGE"}

        elif action == DonnaAction.UPDATE_TASK.value:
            # Just add a comment for now as update
            task_id = decision.get("target_task_id")
            comment = f"<b>Donna:</b> Received related email: \"{email.subject}\". Keeping task updated."
            requests.post(ODOO_SERVICE_URL, json={
                "command": "ADD_COMMENT",
                "task_id": task_id,
                "comment": comment
            })
            result_data = {"success": True, "task_id": task_id, "action": "UPDATED_COMMENT"}

        # 3. ARCHIVE (Learn)
        # Note: In a real system we'd archive the result to memory here
        
        return func.HttpResponse(
            json.dumps({"success": True, "decision": decision, "execution": result_data}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"❌ Donna Conductor Error: {e}", exc_info=True)
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)
