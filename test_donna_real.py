"""
Test Donna with a real email from Luc (no attachments)
This will create a REAL task in Odoo!
"""
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.insert(0, os.path.dirname(__file__))

from StoreProjectOnOdoo.schema.email_payload import EmailPayload
from StoreProjectOnOdoo.core.brain import DonnaBrain


# Realistic email from Luc
email_from_luc = {
    "subject": "Bleckman - Nieuwe interface voor paklijsten",
    "from": "luc.verhoeven@dkm-customs.com",
    "to": "projects@dkm-customs.com",
    "body": """
Hoi,

Bleckman heeft een nieuwe interface nodig voor hun paklijsten.

Ze sturen Excel bestanden via email met de volgende kolommen:
- Artikelnummer
- Omschrijving
- Gewicht (kg)
- Aantal colli
- Land van oorsprong

Wij moeten dit mappen naar ons standaard douane formaat en doorsturen naar hun ERP systeem.

Kunnen jullie dit oppakken? Deadline is eind deze maand.

Groeten,
Luc
    """,
    "bodyPreview": "Bleckman heeft een nieuwe interface nodig voor hun paklijsten...",
    "receivedDateTime": "2026-01-21T11:30:00Z",
    "importance": "normal",
    "attachments": []  # No attachments
}


def main():
    print("="*60)
    print("🤖 DONNA - Creating Real Project from Luc's Email")
    print("="*60)
    
    # Parse email
    print("\n📧 Email Details:")
    print(f"   From: {email_from_luc['from']}")
    print(f"   Subject: {email_from_luc['subject']}")
    print(f"   Attachments: None")
    
    email = EmailPayload.from_dict(email_from_luc)
    
    # Initialize brain
    print("\n🧠 Initializing Donna Brain...")
    brain = DonnaBrain()
    
    # Process (think)
    print("\n🧠 Donna is thinking...")
    context = brain.process(email)
    
    print(f"\n📊 Analysis Results:")
    print(f"   Project Type: {context.project_type.value}")
    print(f"   Task Name: {context.task_name}")
    print(f"   Client: {context.extracted_data.client}")
    print(f"   Flow Type: {context.extracted_data.flow_type}")
    print(f"   Tags: {context.tags}")
    print(f"   Data Sources: {[ds.value for ds in context.data_sources]}")
    print(f"   Priority: {context.priority.value}")
    
    # Confirm before executing
    print("\n" + "="*60)
    confirm = input("⚠️ Create this task in Odoo? (y/n): ")
    
    if confirm.lower() != 'y':
        print("Cancelled.")
        return
    
    # Execute (act)
    print("\n🚀 Donna is executing...")
    result = brain.execute(context)
    
    if result.success:
        print("\n" + "="*60)
        print("✅ SUCCESS! Task Created in Odoo")
        print("="*60)
        print(f"   Task ID: {result.task_id}")
        print(f"   Project ID: {result.project_id}")
        print(f"   Project: {result.project_name}")
        print(f"   Task Name: {result.task_name}")
        print("\n🎉 Go check Odoo!")
    else:
        print("\n" + "="*60)
        print("❌ FAILED!")
        print("="*60)
        print(f"   Error: {result.error}")


if __name__ == "__main__":
    main()
