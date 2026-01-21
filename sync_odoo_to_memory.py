import logging
import sys
import os
import time

# Add paths to access modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OdooSync")

try:
    from OdooService.odoo.client import OdooClient
    from OdooService.config import Config as OdooConfig
    from DonnaMemory.memory_service import MemoryService
except ImportError as e:
    logger.error(f"Import Error: {e}")
    logger.error("Make sure you are running this from the root folder (testAzure)")
    sys.exit(1)

def sync_interface_tasks():
    print("\n" + "="*60)
    print("🔄 SYNC: Odoo 'Interface' Project -> Pinecone Memory")
    print("="*60)
    
    # 1. Connect to Odoo
    print("📡 Connecting to Odoo...")
    try:
        odoo = OdooClient(
            url=OdooConfig.ODOO_URL,
            db=OdooConfig.ODOO_DB,
            username=OdooConfig.ODOO_USERNAME,
            api_key=OdooConfig.ODOO_API_KEY
        )
        odoo.authenticate()
        print("✅ Connected to Odoo")
    except Exception as e:
        logger.error(f"Odoo connection failed: {e}")
        return

    # 2. Get Interface Project
    print("🔍 Finding 'Interface' project...")
    project_ids = odoo.search('project.project', [['name', '=', 'Interface']], limit=1)
    if not project_ids:
        logger.error("Project 'Interface' not found in Odoo!")
        return
    
    interface_project_id = project_ids[0]
    print(f"✅ Found Project ID: {interface_project_id}")

    # 3. Fetch Tasks
    print("📥 Fetching tasks...")
    # Get active tasks with relevant fields
    task_ids = odoo.search('project.task', [
        ['project_id', '=', interface_project_id],
        ['active', '=', True]
    ], limit=100) # Start with 100 to be safe, increase if needed
    
    if not task_ids:
        print("⚠️ No tasks found.")
        return

    tasks = odoo.read('project.task', task_ids, [
        'name', 'description', 'tag_ids', 'partner_id', 'create_date', 'priority'
    ])
    
    print(f"📦 Found {len(tasks)} tasks. Starting sync...")

    # 4. Initialize Memory Service
    memory = MemoryService()
    
    # 5. Process & Upsert
    success_count = 0
    for task in tasks:
        try:
            task_id = task['id']
            task_name = task['name']
            print(f"   Processing: {task_id} - {task_name}")
            
            # --- Map Odoo Data to Schema ---
            
            # Resolve tags (Odoo returns [id, name] or just ids, read usually returns [id, name] for Many2many if configured, but default read returns IDs)
            # Actually standard 'read' returns IDs for M2M. We might need to fetch tag names separately or just ignore specific tag names for now.
            # Let's do a trick: If we want tag names, we need to read them.
            # For simplicity in this bulk sync, we'll try to infer client from name if Partner is missing.
            
            client_name = "Unknown"
            if task['partner_id']: # Tuple [id, name]
                client_name = task['partner_id'][1]
            
            # Simple cleanup of description (remove HTML tags if possible, but raw text is okay for embeddings usually)
            raw_desc = str(task['description'] or "")
            
            # Construct a "ProjectContext"-like dictionary that MemoryService expects
            # MemoryService expects: task_name, extracted_data.client, project_type, tags, description
            
            context = {
                "task_name": task_name,
                "project_type": "INTERFACE", # Since we are syncing Interface project
                "description": raw_desc,
                "tags": [], # We skip resolving tag IDs for speed unless critical
                "extracted_data": {
                    "client": client_name
                },
                "priority": task['priority']
            }
            
            # Upsert
            memory.enrich_from_odoo(context, task_id)
            success_count += 1
            
        except Exception as e:
            logger.error(f"Failed to sync task {task.get('id')}: {e}")
            
    print("\n" + "="*60)
    print(f"✅ SYNC COMPLETE: {success_count}/{len(tasks)} tasks memorized.")
    print("="*60)

if __name__ == "__main__":
    sync_interface_tasks()
