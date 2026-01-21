import azure.functions as func
import logging
import json
import sys
import os

# Ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from DonnaMemory.memory_service import MemoryService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Donna Memory Microservice Endpoint.
    Handles storage and retrieval of project context/memory.
    """
    logger.info('🧠 DonnaMemory: Processing request')
    
    try:
        req_body = req.get_json()
        action = req_body.get('action')
        
        service = MemoryService()
        
        if action == 'enrich_odoo':
            # Handle Odoo Task Storage
            context = req_body.get('context')
            task_id = req_body.get('task_id')
            
            if not context or not task_id:
                return func.HttpResponse(
                    json.dumps({"error": "Missing context or task_id"}), 
                    status_code=400
                )
                
            service.enrich_from_odoo(context, task_id)
            
            return func.HttpResponse(
                json.dumps({"success": True, "message": "Odoo task memorized"}),
                status_code=200
            )
            
        elif action == 'find_duplicate':
            text = req_body.get('text')
            resource_type = req_body.get('resource_type')
            threshold = req_body.get('threshold', 0.8)
            
            duplicate = service.find_duplicate(text, resource_type, threshold)
            
            return func.HttpResponse(
                json.dumps({"success": True, "duplicate": duplicate}),
                status_code=200
            )
            
        elif action == 'search':
            # Handle Search (for testing/future)
            query = req_body.get('query')
            filters = req_body.get('filters')
            
            results = service.search(query, filters)
            
            # Simple serialization of results
            matches = [{"score": m.score, "metadata": m.metadata} for m in results.matches]
            
            return func.HttpResponse(
                json.dumps({"success": True, "results": matches}),
                status_code=200
            )
            
        else:
            return func.HttpResponse(
                json.dumps({"error": f"Unknown action: {action}"}),
                status_code=400
            )
            
    except ValueError:
        return func.HttpResponse(
             json.dumps({"error": "Invalid JSON"}),
             status_code=400
        )
    except Exception as e:
        logger.error(f"Memory Service Error: {e}", exc_info=True)
        return func.HttpResponse(
             json.dumps({"error": str(e)}),
             status_code=500
        )
