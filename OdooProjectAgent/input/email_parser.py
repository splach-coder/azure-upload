import json
import logging
import os
import sys

# Add parent directory to access AI_agents
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from AI_agents.OpenAI.custom_call import CustomCall
from OdooProjectAgent.schema.flow_fingerprint import FlowFingerprint
from OdooProjectAgent.schema.validators import validate_flow

def parse_email_to_flow(email_text: str) -> FlowFingerprint:
    """
    Parses raw email text into a FlowFingerprint using an LLM.
    """
    prompt_path = os.path.join(os.path.dirname(__file__), '../prompts/email_to_flow.txt')
    with open(prompt_path, 'r') as f:
        system_prompt = f.read()

    agent = CustomCall()
    
    # Get response
    response = agent.send_request(system_prompt, email_text)
    
    if not response:
        raise Exception("LLM returned no response")
    
    logging.info(f"LLM Response: {response[:300]}...")
    
    try:
        # Clean potential markdown
        cleaned = response.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        
        # Filter to only valid FlowFingerprint fields
        valid_fields = {
            'client', 'flow_type', 'source', 'subject_used', 'attachments',
            'logic_app', 'azure_function', 'pdf_extraction', 'excel_processing',
            'llm_usage', 'output_format'
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        # Convert to dataclass
        flow = FlowFingerprint(**filtered_data)
        
        # Validate
        validate_flow(flow)
        
        return flow
        
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON: {e}")
        logging.error(f"Raw response: {response}")
        raise Exception(f"Failed to parse LLM response as JSON: {str(e)}")
    except Exception as e:
        logging.error(f"Error creating flow: {e}")
        raise Exception(f"Flow validation/creation failed: {str(e)}")
