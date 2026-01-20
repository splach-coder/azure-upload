from typing import List
from ..schema.flow_fingerprint import FlowFingerprint

def generate_tags(flow: FlowFingerprint) -> List[str]:
    """
    Generates a list of tags based on the flow fingerprint.
    """
    tags = []
    
    # Add standardized tags
    if flow.source:
        tags.append(f"Source: {flow.source}")
    
    if flow.output_format:
        tags.append(f"Output: {flow.output_format}")
        
    # Add dynamic tags based on tools used
    if flow.logic_app:
        tags.append("Logic App")
    
    if flow.azure_function:
        tags.append("Azure Function")
        
    if flow.llm_usage:
        tags.append("AI Enhanced")

    return tags
