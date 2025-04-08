import json

def merge_into_items(first_json_str, second_json_str):
    # Parse the input JSON
    first_data = first_json_str
    second_data = json.loads(second_json_str)
    
    # Create a lookup dictionary for the second JSON using contract_number as the key
    contract_to_data = {obj["contract_number"]: obj for obj in second_data}
    
    # Iterate through each item in the first JSON's Items array
    for item in first_data.get("Items", []):
        other_ref = item.get("other_reference")
        # If a matching contract_number exists, merge the data into the item
        if other_ref in contract_to_data:
            matched_data = contract_to_data[other_ref]
            # Merge matched_data into the item (overwriting existing keys if conflicts occur)
            item.update(matched_data)
    
    # Return the modified first JSON with enriched Items
    return first_data

def transform_afschrijfgegevens(input_data):
    """
    Transform the input data structure by flattening the items array within cost_centers.
    
    Args:
        input_data (dict): The original nested data structure
        
    Returns:
        dict: The transformed data structure
    """
    # Create a deep copy to avoid modifying the original data
    import copy
    result = copy.deepcopy(input_data)
    
    # Check if 'data' and 'pages' exist in the input data
    if 'data' not in result or 'pages' not in result['data']:
        return result
    
    # Process each page
    for page in result['data']['pages']:
        # Check if 'extracted_data' exists in the page
        if 'extracted_data' not in page:
            continue
        
        extracted_data = page['extracted_data']
        
        # Check if 'cost_centers' exists in the extracted data
        if 'cost_centers' not in extracted_data:
            continue
        
        # Process each cost center
        for cost_center in extracted_data['cost_centers']:
            # Check if the cost center has items
            if 'items' in cost_center and isinstance(cost_center['items'], list) and cost_center['items']:
                # Flatten the items array
                for item in cost_center['items']:
                    # Move item properties up to the cost_center level
                    for key, value in item.items():
                        cost_center[key] = value
                
                # Remove the items array
                del cost_center['items']
    
    return extracted_data

def transform_inklaringsdocument(input_data):
    """
    Transform the inklaringsdocument data structure by:
    1. Identifying common fields across all pages
    2. Creating a structure with common fields at the top level
    3. Moving page-specific data to an "Items" array
    
    Args:
        input_data (dict): The original inklaringsdocument data structure
        
    Returns:
        dict: The transformed data structure
    """
    # Initialize the result with metadata
    result = {
    }
    
    # Check if we have pages data
    if "data" not in input_data or "pages" not in input_data["data"] or not input_data["data"]["pages"]:
        return result
    
    pages = input_data["data"]["pages"]
    
    # List of fields that are considered general/common
    general_fields = [
        "License", "Vak 24", "Vak 37", "Vak 44", 
        "vat_importer", "eori_importer", "commercial_reference",
        "incoterm", "place", "entrepot"
    ]
    
    # Extract the first page's data as a baseline
    first_page_data = pages[0].get("extracted_data", {})
    
    # Initialize common_data with all fields from the first page
    common_data = {k: v for k, v in first_page_data.items() if k in general_fields}
    
    # Initialize items array to collect page-specific data
    items = []
    
    # Process each page
    for page in pages:
        page_data = page.get("extracted_data", {})
        
        # Create an item with page-specific fields
        item = {
        }
        
        # Add all fields that are not in common_data
        for k, v in page_data.items():
            if k not in general_fields:
                item[k] = v
        
        # Add this item to the items array
        items.append(item)
    
    # Combine the result
    result.update(common_data)
    result["Items"] = items
    
    result["Vak 44"] = result.get("Vak 44").split('+')
    if len(result["Vak 44"]) > 1:
        result["Vak 44"] = result["Vak 44"][1].strip()
    else:
        result["Vak 44"] = result["Vak 44"][0].strip()    
    
    return result

def split_cost_centers(input_json):
    # Parse the input JSON
    data = input_json
    
    # Extract the parent data (excluding 'cost_centers')
    parent_data = {key: value for key, value in data.items() if key != 'cost_centers'}
    
    # Iterate over each cost_center and merge with parent_data
    output = []
    for cost_center in data.get('cost_centers', []):
        merged_entry = {**parent_data, **cost_center}
        output.append(merged_entry)
    
    # Return the list of merged JSON objects as a formatted JSON string
    return json.dumps(output, indent=2)