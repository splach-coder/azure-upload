
import json


def transform_items_collis(items):
    """
    Transform a list of dictionaries into separate arrays for each field,
    handling newline-separated values by splitting them.
    Only includes HS codes and Gross Weights when they exist.
    
    Args:
        items (list): List of dictionaries containing product information
        
    Returns:
        tuple: Four lists containing product codes, pieces, HS codes, and gross weights
    """
    product_codes = []
    Collis = []
    

    # Second pass: collect only existing HS codes and Gross Weights
    for item in items:
        if "Product Code" in item:
            codes = item["Product Code"].split("\n")
            product_codes.extend(codes)
            
        if "Collis" in item:
            weights = item["Collis"].split("\n")
            Collis.extend(weights)
            
    return [product_codes, Collis]

def arrays_items_collis(arrays):
    """
    Convert parallel arrays into a list of standardized objects.
    Takes corresponding elements from each array to form complete objects.
    
    Args:
        arrays (list): List of lists containing [product_codes, pieces, hs_codes, gross_weights]
    
    Returns:
        list: List of dictionaries with standardized structure
    """
    product_codes, Collis = arrays
    result = []
    
    # Use the length of product codes as base since it's guaranteed to have all items
    if len(product_codes) == len(Collis):
        for i in range(len(product_codes)):
            # Only create object if we have corresponding HS code and Gross Weight
            obj = {
                "Product Code": product_codes[i],
                "Collis": Collis[i],
            }
            result.append(obj)
    else :
        for i in range(len(product_codes)):
            # Only create object if we have corresponding HS code and Gross Weight
            obj = {
                "Product Code": product_codes[i],
                "Collis": 0,
            }
            result.append(obj)

    
    return result

items = [
        {
            "Product Code": "421358"
        },
        {
            "Product Code": "421359",
            "Collis": "6"
        },
        {
            "Product Code": "421360",
            "Collis": "2"
        },
        {
            "Product Code": "421377",
            "Collis": "4\n12"
        },
        {
            "Product Code": "421378"
        }
    ]


data = transform_items_collis(items)
result = arrays_items_collis(data)


print(json.dumps(result, indent=4))





