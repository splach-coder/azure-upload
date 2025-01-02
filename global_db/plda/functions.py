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