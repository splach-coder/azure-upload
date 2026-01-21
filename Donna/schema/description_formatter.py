"""
Donna Schema - Description Formatter
Generates properly formatted Markdown descriptions for Odoo tasks.
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class SubTask:
    """Standard sub-task definition."""
    name: str
    description: str
    order: int


# Standard Interface Project Sub-Tasks
INTERFACE_SUBTASKS = [
    SubTask("Create Logic App", "Set up the Logic App trigger and email processing flow", 1),
    SubTask("Create Azure Function", "Develop the Azure Function for data processing", 2),
    SubTask("Create Document Intelligence Model", "Configure Azure Document Intelligence for extraction", 3),
    SubTask("Add LLM Layer", "Integrate OpenAI/LLM for intelligent extraction", 4),
    SubTask("Create Excel Mapping", "Develop the Excel/data transformation logic", 5),
    SubTask("Testing & Validation", "End-to-end testing with sample documents", 6),
    SubTask("Deploy to Production", "Deploy and configure production environment", 7),
]

# Standard Automation Project Sub-Tasks
AUTOMATION_SUBTASKS = [
    SubTask("Design Workflow", "Document the automation workflow steps", 1),
    SubTask("Create Logic App", "Build the Logic App automation", 2),
    SubTask("Create Azure Function", "Develop supporting Azure Functions", 3),
    SubTask("API Integration", "Connect to external APIs and services", 4),
    SubTask("Error Handling", "Implement retry logic and error notifications", 5),
    SubTask("Testing", "Test with real scenarios", 6),
    SubTask("Deploy & Monitor", "Deploy and set up monitoring/alerts", 7),
]


def format_interface_description(
    client: str,
    flow_type: str,
    summary: str,
    from_address: str,
    subject: str,
    received_at: str,
    attachments: List[str],
    logic_app_name: Optional[str] = None,
    azure_function_name: Optional[str] = None,
    input_format: Optional[str] = None,
    output_format: str = "Excel",
    keywords: Optional[List[str]] = None,
    extra_notes: Optional[str] = None
) -> str:
    """
    Generate properly formatted HTML description for Odoo tasks.
    """
    # Build Logic App name
    if not logic_app_name:
        client_slug = client.lower().replace(' ', '-').replace('_', '-')
        flow_slug = flow_type.lower().replace(' ', '-')[:20]
        logic_app_name = f"la-dkm-{client_slug}-{flow_slug}"
    
    # Build Azure Function name
    if not azure_function_name:
        client_slug = client.lower().replace(' ', '-').replace('_', '-')
        azure_function_name = f"func-dkm-{client_slug}"
    
    atts_str = ", ".join(attachments) if attachments else "None"
    keywords_str = ", ".join(keywords) if keywords else "N/A"
    
    return f"""
    <div>
        <p><b>{summary}</b></p>
        <hr/>
        <h3>📧 Email Metadata</h3>
        <table class="table table-bordered">
            <tr><td><b>From</b></td><td>{from_address}</td></tr>
            <tr><td><b>Subject</b></td><td>{subject}</td></tr>
            <tr><td><b>Received</b></td><td>{received_at}</td></tr>
            <tr><td><b>Attachments</b></td><td>{atts_str}</td></tr>
        </table>
        
        <hr/>
        <h3>🔧 Technical Setup</h3>
        <p><b>Logic App:</b> <code>{logic_app_name}</code></p>
        <p><b>Azure Function:</b> <code>{azure_function_name}</code></p>
        
        <hr/>
        <h3>📊 Data Flow</h3>
        <ul>
            <li><b>Input:</b> {input_format or 'Email with attachments'}</li>
            <li><b>Processing:</b> Azure Function + Document Intelligence</li>
            <li><b>Output:</b> {output_format}</li>
        </ul>
        
        <hr/>
        <h3>🎯 Keywords</h3>
        <p>{keywords_str}</p>
        
        <hr/>
        <h3>✅ Standard Workflow Sub-Tasks created automatically.</h3>
    </div>
    """.strip()


def format_automation_description(
    client: str,
    flow_type: str,
    summary: str,
    from_address: str,
    subject: str,
    received_at: str,
    triggers: Optional[List[str]] = None,
    actions: Optional[List[str]] = None,
    integrations: Optional[List[str]] = None,
    logic_app_name: Optional[str] = None,
    azure_function_name: Optional[str] = None,
    schedule: Optional[str] = None,
    keywords: Optional[List[str]] = None
) -> str:
    """
    Generate properly formatted HTML description for Automation tasks.
    """
    if not logic_app_name:
        client_slug = client.lower().replace(' ', '-').replace('_', '-')
        logic_app_name = f"la-dkm-{client_slug}-automation"
    
    if not azure_function_name:
        client_slug = client.lower().replace(' ', '-').replace('_', '-')
        azure_function_name = f"func-dkm-{client_slug}"
    
    triggers_html = "".join([f"<li>{t}</li>" for t in triggers]) if triggers else "<li>TBD</li>"
    actions_html = "".join([f"<li>{a}</li>" for a in actions]) if actions else "<li>TBD</li>"
    integrations_str = ", ".join(integrations) if integrations else "TBD"
    keywords_str = ", ".join(keywords) if keywords else "N/A"
    
    return f"""
    <div>
        <p><b>{summary}</b></p>
        <hr/>
        <h3>📧 Email Metadata</h3>
        <table class="table table-bordered">
            <tr><td><b>From</b></td><td>{from_address}</td></tr>
            <tr><td><b>Subject</b></td><td>{subject}</td></tr>
            <tr><td><b>Received</b></td><td>{received_at}</td></tr>
        </table>
        
        <hr/>
        <h3>🔧 Technical Setup</h3>
        <p><b>Logic App:</b> <code>{logic_app_name}</code></p>
        <p><b>Azure Function:</b> <code>{azure_function_name}</code></p>
        
        <hr/>
        <h3>⚡ Automation Details</h3>
        <p><b>Triggers:</b></p>
        <ul>{triggers_html}</ul>
        
        <p><b>Actions:</b></p>
        <ul>{actions_html}</ul>
        
        <p><b>Integrations:</b> {integrations_str}</p>
        <p><b>Schedule:</b> {schedule or 'Event-driven'}</p>
        
        <hr/>
        <h3>🎯 Keywords</h3>
        <p>{keywords_str}</p>
        
        <hr/>
        <h3>✅ Standard Workflow Sub-Tasks created automatically.</h3>
    </div>
    """.strip()


def get_subtasks_for_type(project_type: str) -> List[SubTask]:
    """Get standard sub-tasks for a project type."""
    if project_type == "AUTOMATION":
        return AUTOMATION_SUBTASKS
    return INTERFACE_SUBTASKS
