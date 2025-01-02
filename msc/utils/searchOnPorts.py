from global_db.ports.data import ports
from msc.data.bigData import bigData

def search_ports(search_value):
    # Iterate through the list of dictionaries to find the matching port
    for port in ports:
        if port["Port"].lower() == search_value.lower():  # Case-insensitive comparison
            return port["Country Code"]
    
    # If no match is found, return a message
    return ""


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
        if (search_term.lower() in str(entry['container']).lower() and (
            search_term.lower() in str(entry['package']).lower() or
            search_term.lower() in str(entry['net']).lower() or
            search_term.lower() in str(entry['gross']).lower())):
            results = entry
    
    return results