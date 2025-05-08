from datetime import datetime
import copy
import xml.etree.ElementTree as ET
import requests

def transform_json(json_data):
    """
    Function to transform JSON data by merging Sheet1_Items with Sheet3_Logistics
    using multiple fields as matching criteria to handle duplicates
    
    Args:
        json_data (dict): The input JSON data
        
    Returns:
        dict: The transformed JSON with merged data
    """
    # Create a deep copy of the input data
    result = copy.deepcopy(json_data)
    
    # Rename Sheet1_Items to items
    result['items'] = result['Sheet1_Items']
    del result['Sheet1_Items']
    
    # Create a more specific lookup by including all matching fields
    logistics_map = {}
    for item in json_data['Sheet3_Logistics']:
        # Create a unique key using multiple fields to avoid duplicate matches
        key = f"{item['Description']}_{item['Brand']}_{item['HS Code']}_{item['PCS']}_{item['SET']}_{item['CARTON']}"
        logistics_map[key] = item
    
    # Merge data from Sheet3_Logistics into items
    for i, item in enumerate(result['items']):
        # Use the same detailed key for matching
        key = f"{item['Description']}_{item['Brand']}_{item['HS Code']}_{item['PCS']}_{item['SET']}_{item['CARTON']}"
        
        # If we have matching logistics data, add the Gross Weight and Net Weight
        if key in logistics_map:
            result['items'][i]['Gross Weight'] = logistics_map[key]['Gross Weight']
            result['items'][i]['Net Weight'] = logistics_map[key]['Net Weight']
    
    # Remove Sheet3_Logistics from the result
    del result['Sheet3_Logistics']
    
    return result

def merge_items(data):
    # Initialize an empty list to hold all items
    merged_items = []
    
    # Iterate through each contract in the data
    for contract in data:
        # Extend the merged_items list with the items from the current contract
        merged_items.extend(contract['items'])
    
    # Return the merged items as a dictionary
    return {"items": merged_items}

def fetch_exchange_rate(currency_code):
    # Get the current year and month in "YYYYMM" format
    current_date = datetime.now().strftime("%Y%m")

    # Insert the dynamic part into the URL
    url = f"https://www.belastingdienst.nl/data/douane_wisselkoersen/wks.douane.wisselkoersen.dd{current_date}.xml"
    
    # Fetch XML content from the URL
    response = requests.get(url)
    
    if response.status_code == 200:
        # Parse XML content
        root = ET.fromstring(response.content)
        
        # Find the currency block that matches the currency code
        for rate in root.findall("douaneMaandwisselkoers"):
            code = rate.find("muntCode").text
            if code == currency_code:
                foreign_rate = rate.find("tariefInVreemdeValuta").text
                return foreign_rate
    
    return 0.0  # Return None if the currency was not found or request failed