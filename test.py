import xmlrpc.client

ODOO_URL = "https://dkm-customs.odoo.com"
DB = "vva-onniti-dkm-main-20654023"
USERNAME = "anas.benabbou@dkm-customs.com"
API_KEY = "d3f959e2b9dcca8d7180b95c8d673398b8b6040c"

url = ODOO_URL
db = DB
username = USERNAME
api_key = API_KEY

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, api_key, {})

if not uid:
    raise Exception("Odoo authentication failed")

print(f"Authentication successful! User ID: {uid}")

models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# 1. Search for the project "Interface"
print("Searching for project 'Interface'...")
project_ids = models.execute_kw(db, uid, api_key, 'project.project', 'search', [[['name', '=', 'Interface']]])

if project_ids:
    project_id = project_ids[0]
    print(f"Found project 'Interface' with ID: {project_id}")

    # 2. Create a new task in this project
    task_data = {
        'project_id': project_id,
        'name': 'Example Task Created via Script',
        'description': '<p>This is a test task created via the XML-RPC API.</p>',
    }
    
    try:
        task_id = models.execute_kw(db, uid, api_key, 'project.task', 'create', [task_data])
        print(f"Successfully created task with ID: {task_id} in project 'Interface'")
        
        # Read the task back
        task_info = models.execute_kw(db, uid, api_key, 'project.task', 'read', [[task_id], ['name', 'project_id']])
        print("Task Details:", task_info)
        
    except Exception as e:
        print(f"Error creating task: {e}")

else:
    print("Project 'Interface' not found.")
