import sys
import logging
from .config import Config
from .input.email_parser import parse_email_to_flow
from .input.idea_parser import parse_idea_to_flow
from .mapping.project_mapper import project_name, project_description
from .mapping.tag_mapper import generate_tags
from .odoo.client import OdooClient
from .odoo.project_service import ProjectService
from .schema.flow_fingerprint import FlowFingerprint

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Suppress noisy Azure/OpenAI logs
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

def run_agent(input_text: str, input_type: str = "email") -> int:
    """
    Main entry point for the AI Odoo Agent.
    
    Args:
        input_text: The raw input (email body or idea text).
        input_type: "email" or "idea".
        
    Returns:
        int: The ID of the created Odoo project.
    """
    logging.info(f"Starting Agent with input_type={input_type}")
    
    # 1. Parse Input -> Flow Fingerprint
    try:
        if input_type.lower() == "email":
            flow = parse_email_to_flow(input_text)
        elif input_type.lower() == "idea":
            flow = parse_idea_to_flow(input_text)
        else:
            raise ValueError(f"Unknown input_type: {input_type}")
            
        logging.info(f"Flow Fingerprint generated: {flow}")
    except Exception as e:
        logging.error(f"Input parsing failed: {e}")
        raise e

    # 2. Map Fingerprint -> Project Details
    p_name = project_name(flow)
    p_desc = project_description(flow)
    p_tags = generate_tags(flow)
    
    logging.info(f"Mapping complete. Project: '{p_name}'")

    # 3. Execution -> Odoo
    try:
        client = OdooClient(
            url=Config.ODOO_URL,
            db=Config.ODOO_DB,
            username=Config.ODOO_USERNAME,
            api_key=Config.ODOO_API_KEY
        )
        service = ProjectService(client)
        
        project_id = service.create_project(p_name, p_desc, p_tags)
        logging.info(f"Project created successfully. ID: {project_id}")
        return project_id
        
    except Exception as e:
        logging.error(f"Odoo execution failed: {e}")
        raise e

if __name__ == "__main__":
    # Simple CLI usage
    if len(sys.argv) < 2:
        print("Usage: python -m AI_agents.ai_odoo_agent.main <input_text> [email|idea]")
        sys.exit(1)
        
    text = sys.argv[1]
    kind = sys.argv[2] if len(sys.argv) > 2 else "email"
    
    run_agent(text, kind)
