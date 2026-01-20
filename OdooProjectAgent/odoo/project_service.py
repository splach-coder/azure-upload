from .client import OdooClient

def create_task_in_interface(odoo: OdooClient, task_name: str, task_description: str):
    """
    Creates a new task in the 'Interface' project in Odoo.
    Returns the ID of the created task.
    No logic here. Just execution.
    """
    # Ensure authentication
    if not odoo.uid:
        odoo.authenticate()
    
    # First, find the Interface project
    project_ids = odoo.models.execute_kw(
        odoo.db, odoo.uid, odoo.api_key,
        'project.project', 'search',
        [[['name', '=', 'Interface']]]
    )
    
    if not project_ids:
        raise Exception("Project 'Interface' not found in Odoo")
    
    project_id = project_ids[0]
    
    # Create the task
    task_data = {
        'project_id': project_id,
        'name': task_name,
        'description': task_description
    }
    
    task_id = odoo.create('project.task', task_data)
    return task_id, project_id
