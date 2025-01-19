from global_db.plda.bigData import bigData

def search_json(search_term):
    """
    Search for entries in the JSON array based on the search term.
    
    Parameters:
    - data: List of dictionaries (the JSON array).
    - search_term: The term to search for in the JSON entries.

    Returns:
    - JSON object of matching entries.
    """
    results = {}
    
    # Iterate through each entry in the data
    for entry in bigData:
        # Check if the search term is in any of the values (case insensitive)
        if (search_term.lower() == str(entry['container']).lower()):
            results = entry
    
    return results


from .bigData import bigData  # Import the bigData array

def append_container_data(new_container):
    """
    Append new container data to bigData array and save to file
    """
    try:
        # Validate required fields
        required_fields = ['container', 'package', 'net', 'gross']
        if not all(field in new_container for field in required_fields):
            raise ValueError("Missing required fields")
            
        # Append new data
        bigData.append(new_container)
        
        # Save to file
        save_to_file()
        
        print(f"Data appended successfully: {new_container}")
        return True
    except Exception as e:
        print(f"Error appending data: {str(e)}")
        return False

def save_to_file():
    """Save bigData to the Python file"""
    try:
        file_path = 'global_db/plda/bigData.py'
        with open(file_path, 'w') as f:
            f.write('bigData = [\n')
            for item in bigData:
                f.write(f'    {{\n')
                f.write(f'        "container": "{item["container"]}",\n')
                f.write(f'        "package": {item["package"]},\n')
                f.write(f'        "net": {item["net"]},\n')
                f.write(f'        "gross": {item["gross"]}\n')
                f.write('    },\n')
            f.write(']\n')
        return True
    except Exception as e:
        print(f"Error saving to file: {str(e)}")
        return False