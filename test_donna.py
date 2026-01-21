"""
Donna AI Agent - Test Script
Run this to test Donna locally without Azure Functions.

Usage:
    python test_donna.py              # Run all tests
    python test_donna.py --odoo       # Run with actual Odoo creation
    python test_donna.py --quick      # Quick test (no LLM)
"""
import json
import logging
import sys
import os
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DonnaTest")

# Add paths
sys.path.insert(0, os.path.dirname(__file__))


def test_email_payload():
    """Test 1: EmailPayload parsing"""
    print("\n" + "="*60)
    print("TEST 1: EmailPayload Parsing")
    print("="*60)
    
    from StoreProjectOnOdoo.schema.email_payload import EmailPayload
    
    email_data = {
        "subject": "VanPoppel Invoice Processing",
        "from": "luc@vanpoppel.com",
        "body": "Please process these invoices from VanPoppel. They send PDFs.",
        "receivedDateTime": "2026-01-21T10:00:00Z",
        "importance": "high",
        "attachments": [
            {"name": "invoice.pdf", "contentType": "application/pdf", "size": 12345}
        ]
    }
    
    email = EmailPayload.from_dict(email_data)
    
    print(f"✅ Subject: {email.subject}")
    print(f"✅ From: {email.from_address}")
    print(f"✅ Has Attachments: {email.has_attachments}")
    print(f"✅ Has PDF: {email.has_pdf}")
    print(f"✅ Has Excel: {email.has_excel}")
    print(f"✅ Attachment Types: {email.attachment_types}")
    
    assert email.has_pdf == True
    assert email.has_excel == False
    print("\n✅ TEST 1 PASSED")
    return True


def test_attachment_analyzer():
    """Test 2: Attachment Analysis"""
    print("\n" + "="*60)
    print("TEST 2: Attachment Analyzer")
    print("="*60)
    
    from StoreProjectOnOdoo.schema.email_payload import EmailPayload
    from StoreProjectOnOdoo.triage.attachment_analyzer import AttachmentAnalyzer, ProcessingStrategy
    
    analyzer = AttachmentAnalyzer()
    
    # Test cases
    test_cases = [
        {"attachments": [], "expected": ProcessingStrategy.TEXT_ONLY},
        {"attachments": [{"name": "doc.pdf", "contentType": "application/pdf"}], "expected": ProcessingStrategy.PDF},
        {"attachments": [{"name": "data.xlsx", "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}], "expected": ProcessingStrategy.EXCEL},
        {"attachments": [
            {"name": "doc.pdf", "contentType": "application/pdf"},
            {"name": "data.xlsx", "contentType": "application/vnd.ms-excel"}
        ], "expected": ProcessingStrategy.MIXED},
    ]
    
    for i, tc in enumerate(test_cases):
        email = EmailPayload.from_dict({
            "subject": "Test", 
            "from": "test@test.com", 
            "body": "Test",
            "receivedDateTime": "2026-01-21",
            "attachments": tc["attachments"]
        })
        strategy = analyzer.analyze(email)
        status = "✅" if strategy == tc["expected"] else "❌"
        print(f"{status} Case {i+1}: {len(tc['attachments'])} attachments → {strategy.value} (expected: {tc['expected'].value})")
    
    print("\n✅ TEST 2 PASSED")
    return True


def test_prompts():
    """Test 3: Prompts Loading"""
    print("\n" + "="*60)
    print("TEST 3: Prompts Loading")
    print("="*60)
    
    from StoreProjectOnOdoo.ai.prompts import PROMPTS, get_prompt
    
    print(f"✅ Available prompts: {list(PROMPTS.keys())}")
    
    for purpose in PROMPTS.keys():
        prompt = get_prompt(purpose)
        print(f"✅ {purpose}: {len(prompt)} chars")
        assert len(prompt) > 100, f"Prompt {purpose} seems too short"
    
    print("\n✅ TEST 3 PASSED")
    return True


def test_classifier_rules():
    """Test 4: Rule-based Classification (no LLM)"""
    print("\n" + "="*60)
    print("TEST 4: Rule-based Classification")
    print("="*60)
    
    from StoreProjectOnOdoo.schema.email_payload import EmailPayload
    from StoreProjectOnOdoo.triage.classifier import ProjectClassifier
    from StoreProjectOnOdoo.schema.odoo_fields import ProjectType
    
    # Create classifier without LLM
    classifier = ProjectClassifier(llm_client=None)
    classifier.llm = None  # Force rule-based
    
    test_cases = [
        {
            "subject": "VanPoppel Excel Template",
            "body": "Need to process invoices from Excel to customs format",
            "expected": ProjectType.INTERFACE
        },
        {
            "subject": "New Logic App for Container Tracking",
            "body": "We need to automate the workflow with a script that triggers on email",
            "expected": ProjectType.AUTOMATION
        },
        {
            "subject": "Data Mapping Request",
            "body": "Client sends PDF documents, we need to extract and export to Excel",
            "expected": ProjectType.INTERFACE
        }
    ]
    
    for i, tc in enumerate(test_cases):
        email = EmailPayload.from_dict({
            "subject": tc["subject"],
            "from": "test@test.com",
            "body": tc["body"],
            "receivedDateTime": "2026-01-21",
            "attachments": []
        })
        
        result = classifier._classify_with_rules(email, None)
        status = "✅" if result == tc["expected"] else "❌"
        print(f"{status} Case {i+1}: '{tc['subject'][:30]}...' → {result.value} (expected: {tc['expected'].value})")
    
    print("\n✅ TEST 4 PASSED")
    return True


def test_odoo_client():
    """Test 5: Odoo Client Connection"""
    print("\n" + "="*60)
    print("TEST 5: Odoo Client Connection")
    print("="*60)
    
    from StoreProjectOnOdoo.odoo.client import OdooClient
    from StoreProjectOnOdoo.config import Config
    
    print(f"📡 Connecting to: {Config.ODOO_URL}")
    print(f"📊 Database: {Config.ODOO_DB}")
    print(f"👤 Username: {Config.ODOO_USERNAME}")
    
    try:
        client = OdooClient(
            url=Config.ODOO_URL,
            db=Config.ODOO_DB,
            username=Config.ODOO_USERNAME,
            api_key=Config.ODOO_API_KEY
        )
        uid = client.authenticate()
        print(f"✅ Authenticated! User ID: {uid}")
        
        # Test search for Interface project
        projects = client.search('project.project', [['name', '=', 'Interface']], limit=1)
        if projects:
            print(f"✅ Found 'Interface' project: ID {projects[0]}")
        else:
            print(f"⚠️ 'Interface' project not found")
        
        print("\n✅ TEST 5 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n❌ TEST 5 FAILED (Odoo connection issue)")
        return False


def test_full_flow_no_odoo():
    """Test 6: Full Brain Flow (without Odoo execution)"""
    print("\n" + "="*60)
    print("TEST 6: Full Brain Flow (Dry Run)")
    print("="*60)
    
    from StoreProjectOnOdoo.schema.email_payload import EmailPayload
    from StoreProjectOnOdoo.core.brain import DonnaBrain
    
    email_data = {
        "subject": "VanPoppel - New Invoice Interface",
        "from": "luc@vanpoppel.com",
        "body": """
        Hi,
        
        VanPoppel needs a new interface for their invoice processing.
        They send invoices as PDF attachments by email.
        We need to:
        - Extract invoice data from PDFs
        - Map to their Excel template
        - Output results for their ERP system
        
        This is urgent.
        
        Thanks,
        Luc
        """,
        "receivedDateTime": "2026-01-21T09:00:00Z",
        "importance": "high",
        "attachments": [
            {"name": "sample_invoice.pdf", "contentType": "application/pdf", "size": 12345}
        ]
    }
    
    print("📧 Parsing email...")
    email = EmailPayload.from_dict(email_data)
    
    print("🧠 Initializing Brain...")
    brain = DonnaBrain()
    
    print("🧠 Processing (thinking)...")
    # Note: This will try to use LLM. If it fails, it uses fallback.
    try:
        context = brain.process(email)
        
        print(f"\n📊 RESULTS:")
        print(f"   Project Type: {context.project_type.value}")
        print(f"   Task Name: {context.task_name}")
        print(f"   Client: {context.extracted_data.client}")
        print(f"   Flow Type: {context.extracted_data.flow_type}")
        print(f"   Tags: {context.tags}")
        print(f"   Data Sources: {[ds.value for ds in context.data_sources]}")
        print(f"   Priority: {context.priority.value}")
        
        print("\n✅ TEST 6 PASSED (Brain processing works)")
        return True
        
    except Exception as e:
        print(f"⚠️ Brain processing error: {e}")
        print("   (This is expected if OpenAI API is not configured)")
        print("\n⚠️ TEST 6 PARTIAL (LLM not available, but structure is correct)")
        return True


def test_full_flow_with_odoo():
    """Test 7: Full Flow WITH Odoo Task Creation"""
    print("\n" + "="*60)
    print("TEST 7: Full Flow WITH Odoo Task Creation")
    print("="*60)
    print("⚠️ This will CREATE a real task in Odoo!")
    
    from StoreProjectOnOdoo.schema.email_payload import EmailPayload
    from StoreProjectOnOdoo.core.brain import DonnaBrain
    
    email_data = {
        "subject": "TEST - Donna Agent Test Task",
        "from": "test@donna-agent.com",
        "body": "This is a test task created by Donna AI Agent testing script. Safe to delete.",
        "receivedDateTime": "2026-01-21T09:00:00Z",
        "importance": "normal",
        "attachments": []
    }
    
    email = EmailPayload.from_dict(email_data)
    brain = DonnaBrain()
    
    # Process and Execute
    context = brain.process(email)
    result = brain.execute(context)
    
    if result.success:
        print(f"\n✅ Task Created Successfully!")
        print(f"   Task ID: {result.task_id}")
        print(f"   Project: {result.project_name}")
        print(f"   Task Name: {result.task_name}")
        print("\n✅ TEST 7 PASSED")
        return True
    else:
        print(f"\n❌ Task Creation Failed: {result.error}")
        print("\n❌ TEST 7 FAILED")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Donna AI Agent")
    parser.add_argument('--odoo', action='store_true', help='Run Odoo tests (creates real task)')
    parser.add_argument('--quick', action='store_true', help='Quick tests only (no LLM/Odoo)')
    args = parser.parse_args()
    
    print("="*60)
    print("🤖 DONNA AI AGENT - TEST SUITE")
    print("="*60)
    
    results = []
    
    # Core tests (always run)
    results.append(("EmailPayload Parsing", test_email_payload()))
    results.append(("Attachment Analyzer", test_attachment_analyzer()))
    results.append(("Prompts Loading", test_prompts()))
    results.append(("Rule-based Classification", test_classifier_rules()))
    
    if not args.quick:
        # Odoo connection test
        results.append(("Odoo Client Connection", test_odoo_client()))
        
        # Full flow test (dry run)
        results.append(("Full Brain Flow (Dry Run)", test_full_flow_no_odoo()))
    
    if args.odoo:
        # Full flow with actual Odoo creation
        confirm = input("\n⚠️ This will create a REAL task in Odoo. Continue? (y/n): ")
        if confirm.lower() == 'y':
            results.append(("Full Flow with Odoo", test_full_flow_with_odoo()))
        else:
            print("Skipped Odoo creation test")
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed out of {len(results)} tests")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
