import logging
from global_db.plda.functions import search_json


def process_container_data(input_data: dict) -> list:
    """
    Transform container data by flattening the structure and converting data types.
    
    Args:
        input_data (dict): Input dictionary containing vessel info and container array
        
    Returns:
        list: Array of processed container objects
        
    Raises:
        ValueError: If required fields are missing or data types are invalid
    """
    try:
        # Validate required fields
        required_fields = ['vissel', 'stay', 'loyd', 'containers']
        if not all(field in input_data for field in required_fields):
            missing = [f for f in required_fields if f not in input_data]
            raise ValueError(f"Missing required fields: {missing}")
            
        # Extract common fields
        common_fields = {
            'vissel': input_data['vissel'],
            'stay': input_data['stay'],
            'loyd': input_data['loyd']
        }
        
        result = []
        for container in input_data['containers']:
            # Create new container object with common fields
            processed_container = common_fields.copy()
            
            # Add container-specific fields
            processed_container.update(container)
            
            # Convert Packages to integer
            if 'Packages' in processed_container:
                try:
                    processed_container['Packages'] = int(processed_container['Packages'])
                except ValueError:
                    processed_container['Packages'] = 0
                    
            if 'BLnumber' in processed_container:
                processed_container['BLnumber'] = processed_container['BLnumber'].replace(' ', '')
                
            if 'Origin' in processed_container:
                processed_container['Origin'] = processed_container['Origin'][:2]
            
            result.append(processed_container)
            
        return result
        
    except Exception as e:
        raise ValueError(f"Error processing container data: {str(e)}")
    
def transform_container_data(input_data: list) -> list:
    """
    Transform container data to conform to specified schema with additional fields.
    
    Args:
        input_data (list): List of container dictionaries
        
    Returns:
        list: Transformed container data with additional fields
    """
    if not input_data:
        return []
        
    result = []
    for container in input_data:
        
        data = search_json(container.get("containers"))
        
        gross, net = 0.00, 0.00
        
        if data and  container.get("Packages") == data.get("package"):
            gross, net = data.get("gross"), data.get("net")
        
        transformed = {
            **container,
            "Quay": "BEKOUAZ03318024",
            "globalWeight":gross,
            "globalWeight2":net,
            "items": [{
                "item": 1,
                "ArrivalNotice1": f"1{container.get('stay')}L{container.get('loyd')}*{container.get('Article Nbr').zfill(4)}",
                "ArrivalNotice2": f"ANFREI*1*{container.get('BLnumber')}",
                "container": container.get("containers"),
                "Description": container.get("Description"),
                "Packages": container.get("Packages"),
                "Gross Weight": gross,
                "Net Weight": net,
            }]
        }
        result.append(transformed)
        
        
        
    return result


def fill_missing_container_values(data: dict) -> dict:
    """
    Fill missing values in container objects based on previous container data.
    
    Args:
        data (dict): Dictionary containing array of container objects
        
    Returns:
        dict: Processed data with filled missing values
    """
    if not data or 'containers' not in data or not data['containers']:
        return data
        
    containers = data['containers']
    fields_to_check = ['Description', 'BLnumber', 'Origin']
    
    # Process each container
    for i, current in enumerate(containers):
        if i == 0:
            continue
            
        previous = containers[i-1]
        
        # Fill missing values from previous container
        for field in fields_to_check:
            if not current.get(field):
                current[field] = previous.get(field, '')
                
    return data      
        
        
        
        
        
        
        
        
        
        
        
        
        
          