import json
import os
import sys

# Add parent directory to path to import CustomCall
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from AI_agents.OpenAI.custom_call import CustomCall
from AI_agents.ai_odoo_agent.schema.flow_fingerprint import FlowFingerprint
from AI_agents.ai_odoo_agent.schema.validators import validate_flow

def parse_idea_to_flow(idea_text: str) -> FlowFingerprint:
    """
    Parses raw idea text into a FlowFingerprint using an LLM.
    """
    prompt_path = os.path.join(os.path.dirname(__file__), '../prompts/idea_to_flow.txt')
    with open(prompt_path, 'r') as f:
        system_prompt = f.read()

    agent = CustomCall()
    
    response_json_str = agent.send_request(system_prompt, idea_text)
    
    if not response_json_str:
        raise Exception("LLM returned no response")

    try:
        # Clean potential markdown
        cleaned_response = response_json_str.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned_response)
        
        # Convert to dataclass
        flow = FlowFingerprint(**data)
        
        # Validate
        validate_flow(flow)
        
        return flow
    except json.JSONDecodeError:
        raise Exception(f"Failed to parse LLM response as JSON: {response_json_str}")
    except Exception as e:
        raise Exception(f"Flow validation/creation failed: {e}")
