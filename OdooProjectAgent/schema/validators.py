from .flow_fingerprint import FlowFingerprint

def validate_flow(flow: FlowFingerprint):
    """
    Validates the FlowFingerprint to ensure strict adherence to the schema.
    If validation fails, raising an error stops the agent immediately.
    """
    if not flow.client:
        raise ValueError("Client name is missing.")
    
    if not flow.flow_type:
        raise ValueError("Flow type is missing.")

    valid_sources = ["Email", "HTTP", "Blob"]
    if flow.source not in valid_sources:
        raise ValueError(f"Invalid source '{flow.source}'. Must be one of {valid_sources}.")

    valid_outputs = ["Excel", "JSON", "XML"]
    if flow.output_format not in valid_outputs:
        raise ValueError(f"Invalid output_format '{flow.output_format}'. Must be one of {valid_outputs}.")

    if flow.attachments is None:
        raise ValueError("Attachments list cannot be None.")

    return True
