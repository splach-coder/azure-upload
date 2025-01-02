import openpyxl
import json

def excel_to_json(file_path, json_file_path):
    try:
        # Load the workbook and select the active sheet
        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active

        # Initialize a list to hold the data
        data = []

        # Iterate through the rows in the sheet
        for row in sheet.iter_rows(min_row=4, values_only=True):  # Assuming the first row is a header
            if row[0] is not None:  # Ensure the first column (A) has data
                entry = {
                    'container': row[1],  # Column A
                    'package': row[0],    # Column B
                    'net': row[2],        # Column C
                    'gross': row[3]       # Column D
                }
                data.append(entry)

        # Write the data to a JSON file
        with open(json_file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        return data  # Return the data as a JSON array

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def search_json(data, search_term):
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
    for entry in data:
        # Check if the search term is in any of the values (case insensitive)
        if (search_term.lower() in str(entry['container']).lower() or
            search_term.lower() in str(entry['package']).lower() or
            search_term.lower() in str(entry['net']).lower() or
            search_term.lower() in str(entry['gross']).lower()):
            results = entry
    
    return results

excel_to_json("FOLLOW UP CASA (1).xlsx", "data.json")
