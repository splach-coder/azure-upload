"""
Odoo Service - Pure Worker
Responsible for Odoo CRUD operations only. No AI/Intelligence here.
"""
import azure.functions as func
import logging
import json
import sys
import os

# Add paths for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from OdooService.odoo.client import OdooClient
from OdooService.odoo.project_service import ProjectService
from OdooService.config import Config

logger = logging.getLogger(__name__)

async def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('⚙️ OdooService: Processing command')
    
    try:
        body = req.get_json()
        command = body.get("command")
        
        if not command:
            return func.HttpResponse(json.dumps({"error": "No command provided"}), status_code=400)

        # Initialize Odoo Client
        client = OdooClient(Config.ODOO_URL, Config.ODOO_DB, Config.ODOO_USERNAME, Config.ODOO_API_KEY)
        client.authenticate()
        project_service = ProjectService(client)

        if command == "CREATE_TASK":
            # Extract data
            project_name = body.get("project_name", "Interface")
            task_name = body.get("task_name")
            description = body.get("description", "")
            
            task_id, project_id = project_service.create_task(
                project_name=project_name,
                task_name=task_name,
                description=description
            )
            return func.HttpResponse(json.dumps({"success": True, "task_id": task_id}), status_code=200)

        elif command == "UPDATE_TASK":
            task_id = body.get("task_id")
            updates = body.get("updates", {})
            success = project_service.update_task(task_id, **updates)
            return func.HttpResponse(json.dumps({"success": success}), status_code=200)

        elif command == "MOVE_STAGE":
            task_id = body.get("task_id")
            stage_name = body.get("stage_name")
            success = project_service.move_task_to_stage(task_id, stage_name)
            return func.HttpResponse(json.dumps({"success": success}), status_code=200)

        elif command == "ADD_COMMENT":
            task_id = body.get("task_id")
            comment = body.get("comment")
            success = project_service.add_task_comment(task_id, comment)
            return func.HttpResponse(json.dumps({"success": success}), status_code=200)

        elif command == "SEND_MESSAGE":
            task_id = body.get("task_id")
            message = body.get("message")
            success = project_service.send_task_message(task_id, message)
            return func.HttpResponse(json.dumps({"success": success}), status_code=200)

        else:
            return func.HttpResponse(json.dumps({"error": f"Unknown command: {command}"}), status_code=400)

    except Exception as e:
        logger.error(f"❌ OdooService Error: {e}", exc_info=True)
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)
