import logging
import re
from global_db.functions.numbers.functions import safe_float_conversion, safe_int_conversion
from global_db.plda.functions import search_json

def fill_items_with_article_parse_numbers(result):
    #get items from result 
    items = result.get("Items", "")
    Article = result.get("Article", "")
    BLnumber = result.get("BLnumber", "")

    for item in items:
        item["Article"] = Article
        item["BLnumber"] = BLnumber
        item["Gross"] = safe_float_conversion(item.get("Gross", ""))
        item["Package"] = safe_int_conversion(item.get("Package", ""))

    return result    

def group_data_with_container(input_data):
    # Create a base object with all fields except 'Items'
    base = {key: value for key, value in input_data.items() if key != 'Items'}
    
    # Group items by container
    container_groups = {}
    for item in input_data['Items']:
        container = item['Container']
        if container not in container_groups:
            container_groups[container] = []
        container_groups[container].append(item)
    
    # Create transformed objects
    transformed = []
    for container, items in container_groups.items():
        new_obj = base.copy()
        new_obj['Container'] = container
        new_obj['Items'] = items
        transformed.append(new_obj)
    
    return transformed   
