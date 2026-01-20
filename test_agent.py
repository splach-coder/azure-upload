import sys
import os

# Ensure the root directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AI_agents.ai_odoo_agent.main import run_agent

def test_email_flow():
    print("--- Testing Email Input ---")
    email_text = """
    From: Luc
    Subject: New Project: ACME Invoice Processing with ref 123
    
    Hi,
    I need a new flow for ACME. They will send PDFs and Excels by email.
    We need to extract data using Azure AI Document Intelligence and process it with a Logic App named 'la-acme-ingestion'.
    Output should be an Excel file.
    """
    
    try:
        project_id = run_agent(email_text, "email")
        print(f"✅ Email Test Passed. Project ID: {project_id}")
    except Exception as e:
        print(f"❌ Email Test Failed: {e}")

def test_idea_flow():
    print("\n--- Testing Idea Input ---")
    idea_text = "Internal tool to scan receipts from blob storage and save to JSON. Client is Internal."
    
    try:
        project_id = run_agent(idea_text, "idea")
        print(f"✅ Idea Test Passed. Project ID: {project_id}")
    except Exception as e:
        print(f"❌ Idea Test Failed: {e}")

if __name__ == "__main__":
    test_email_flow()
    # test_idea_flow() 
