from msc.data.data import ports

def search_ports(search_value):
    # Iterate through the list of dictionaries to find the matching port
    for port in ports:
        if port["Port"].lower() == search_value.lower():  # Case-insensitive comparison
            return port["Country Code"]
    
    # If no match is found, return a message
    return ""