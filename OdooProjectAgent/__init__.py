import azure.functions as func
import logging
import json
import sys
import os
from datetime import datetime

# Add paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from OdooProjectAgent.input.email_parser import parse_email_to_flow
from OdooProjectAgent.mapping.project_mapper import project_name, project_description
from OdooProjectAgent.odoo.client import OdooClient
from OdooProjectAgent.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress noisy logs
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function to process email requests from Logic Apps and create Odoo projects.
    
    Expected JSON payload from Logic Apps:
    {
        "from": "luc@company.com",
        "to": "projects@company.com",
        "subject": "New Project: ACME Invoice Processing",
        "body": "Email body text...",
        "bodyPreview": "First 100 chars preview...",
        "hasAttachments": true,
        "attachments": [
            {
                "name": "invoice.pdf",
                "contentType": "application/pdf",
                "size": 12345
            }
        ],
        "receivedDateTime": "2026-01-20T15:00:00Z",
        "importance": "high"
    }
    """
    logger.info('🤖 OdooProjectAgent: Processing incoming email request')

    try:
        # Parse request body
        try:
            body = req.get_json()
        except ValueError:
            logger.error("Invalid JSON in request body")
            return func.HttpResponse(
                body=json.dumps({"error": "Invalid JSON format"}),
                status_code=400,
                mimetype="application/json"
            )

        # Extract email data (flexible - support both simple and full schemas)
        email_from = body.get('from', 'Unknown Sender')
        email_to = body.get('to', '')
        subject = body.get('subject', '')
        email_body = body.get('body', body.get('email_body', ''))  # Support both
        body_preview = body.get('bodyPreview', '')
        has_attachments = body.get('hasAttachments', False)
        attachments = body.get('attachments', [])
        received_time = body.get('receivedDateTime', '')
        importance = body.get('importance', 'normal')

        if not email_body:
            logger.warning("No email body provided")
            return func.HttpResponse(
                body=json.dumps({"error": "email body is required"}),
                status_code=400,
                mimetype="application/json"
            )

        # Build rich context for the AI
        attachment_names = []
        attachment_types = []
        
        if isinstance(attachments, list):
            for att in attachments:
                if isinstance(att, dict):
                    attachment_names.append(att.get('name', ''))
                    content_type = att.get('contentType', '')
                    if 'pdf' in content_type.lower():
                        attachment_types.append('PDF')
                    elif 'excel' in content_type.lower() or 'spreadsheet' in content_type.lower():
                        attachment_types.append('Excel')
                elif isinstance(att, str):
                    attachment_names.append(att)
                    if att.lower().endswith('.pdf'):
                        attachment_types.append('PDF')
                    elif att.lower().endswith(('.xlsx', '.xls', '.csv')):
                        attachment_types.append('Excel')
        
        # Remove duplicates
        attachment_types = list(set(attachment_types))

        # Construct enriched email text for AI parsing
        enriched_email = f"""
FROM: {email_from}
TO: {email_to}
SUBJECT: {subject}
RECEIVED: {received_time}
IMPORTANCE: {importance}
HAS ATTACHMENTS: {has_attachments}
ATTACHMENT FILES: {', '.join(attachment_names) if attachment_names else 'None'}

EMAIL BODY:
{email_body}
""".strip()

        logger.info(f"📧 Processing email from: {email_from}")
        logger.info(f"📋 Subject: {subject}")
        logger.info(f"📎 Attachments: {len(attachment_names)}")

        # Step 1: Parse Email -> Flow Fingerprint
        try:
            flow = parse_email_to_flow(enriched_email)
            
            # Override attachments with detected types if AI didn't catch them
            if not flow.attachments and attachment_types:
                flow.attachments = attachment_types
            
            logger.info(f"✅ Flow Fingerprint created: {flow.client} - {flow.flow_type}")
        except Exception as e:
            logger.error(f"❌ Email parsing failed: {e}")
            return func.HttpResponse(
                body=json.dumps({
                    "error": "Failed to parse email",
                    "details": str(e),
                    "email_preview": body_preview[:100] if body_preview else subject
                }),
                status_code=500,
                mimetype="application/json"
            )

        # Step 2: Map to Odoo Task Details
        task_name = project_name(flow)
        task_desc = project_description(flow)

        # Add email metadata to description
        task_desc += f"\n\n---\nEmail Metadata:\nFrom: {email_from}\nReceived: {received_time}\nAttachments: {', '.join(attachment_names) if attachment_names else 'None'}"

        logger.info(f"🗺️ Task mapped: '{task_name}'")

        # Step 3: Create Task in Interface Project
        try:
            client = OdooClient(
                url=Config.ODOO_URL,
                db=Config.ODOO_DB,
                username=Config.ODOO_USERNAME,
                api_key=Config.ODOO_API_KEY
            )
            
            from OdooProjectAgent.odoo.project_service import create_task_in_interface
            task_id, project_id = create_task_in_interface(client, task_name, task_desc)
            logger.info(f"✅ Odoo Task created successfully. Task ID: {task_id} in Project 'Interface' (ID: {project_id})")

            # Return success response
            return func.HttpResponse(
                body=json.dumps({
                    "success": True,
                    "task_id": task_id,
                    "project_id": project_id,
                    "project_name": "Interface",
                    "task_name": task_name,
                    "flow_fingerprint": {
                        "client": flow.client,
                        "flow_type": flow.flow_type,
                        "source": flow.source,
                        "output_format": flow.output_format,
                        "attachments": flow.attachments
                    },
                    "email_metadata": {
                        "from": email_from,
                        "subject": subject,
                        "received": received_time,
                        "attachment_count": len(attachment_names)
                    }
                }),
                status_code=200,
                mimetype="application/json"
            )

        except Exception as e:
            logger.error(f"❌ Odoo task creation failed: {e}")
            return func.HttpResponse(
                body=json.dumps({
                    "error": "Failed to create Odoo task",
                    "details": str(e),
                    "task_name": task_name
                }),
                status_code=500,
                mimetype="application/json"
            )

    except Exception as e:
        logger.error(f"❌ Unhandled exception: {e}", exc_info=True)
        return func.HttpResponse(
            body=json.dumps({
                "error": "Internal server error",
                "details": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )
