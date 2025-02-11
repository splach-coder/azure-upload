def fill_missing_container_values(data: dict) -> dict:
    """
    Fill missing values in container objects based on previous container data.
    
    Args:
        data (dict): Dictionary containing array of container objects
        
    Returns:
        dict: Processed data with filled missing values
    """
    if not data or 'Items' not in data or not data['Items']:
        return data
        
    containers = data.get('Items')
    fields_to_check = ['Container']
    
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

def clean_data(data: dict) -> dict:
    """
    clean the data from spacesm cast to numbers to int nd floats
    
    Args:
        data (dict): Dictionary containing array of container objects
        
    Returns:
        dict: Processed data cleaned values
    """
    if not data or 'Items' not in data or not data['Items']:
        return data
        
    items = data.get('Items')

    for item in items:
        if 'Container' in item and item.get('Container'):
            Container = item.get('Container').replace(' ', '')
            Container = Container if validate_container_number(Container) else ""
            item["Container"] = Container
            
        if 'KGM' in item and item.get('KGM'):
            item['KGM'] = float(item.get('KGM').replace(' ', '').replace(',', '.'))

        if 'Packages' in item and item.get('Packages'):
            package = item.get('Packages').replace(' ', '').split('\n')
            package = [int(num) for num in package]
            item['Packages'] = sum(package)
            
        if 'ArticleNumber' in item and item.get('ArticleNumber'):
            articlenumber = item.get('ArticleNumber')[0:3]
            itemnumber = item.get('ArticleNumber')[3:]
            item['ArticleNumber'] = articlenumber
            item['ItemNumber'] = itemnumber

    return data

def validate_container_number(container_number):
  """
  Validates a container number.

  Args:
    container_number (str): The container number to validate.

  Returns:
    bool: True if the container number is valid, False otherwise.
  """
  # Check if the container number has the correct length
  if len(container_number) != 11:
    return False

  # Check if the container number starts with 4 letters
  if not container_number[:4].isalpha():
    return False

  # Check if the container number has 6 digits
  if not container_number[4:10].isdigit():
    return False

  # Check if the container number has a check digit
  if not container_number[10].isdigit():
    return False

  return True