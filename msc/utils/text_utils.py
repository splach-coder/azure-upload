import re
import json

def swap_number_string(text):
    text = re.sub(r'\s+', ' ', text).strip()
    match = re.match(r"(\d+)\s*(.*)", text)
    if match:
        number = match.group(1)
        remaining_string = match.group(2)
        return f"{remaining_string} {number}"
    else:
        return text

def switch_number_and_string(text):
    cleaned_text = re.sub(r'\s+', ' ', text).strip()
    match = re.match(r"(\D+)\s*(\d+)", cleaned_text)
    if match:
        string_part = match.group(1).strip()
        number_part = match.group(2).strip()
        return f"{number_part} {string_part}"
    else:
        return cleaned_text

def remove_control_chars(text):
    return ''.join(char for char in text if ord(char) >= 32 and ord(char) != 127)

def extract_numbers(input_string):
    # Use a regular expression to find all digits in the string
    numbers = re.sub(r'\D', '', input_string)
    return numbers

def extract_numbers_from_string(input_string):
    # Use regular expression to find all numbers in the string
    numbers = re.findall(r'\d+', input_string)
    
    # Convert the numbers from string to integers
    numbers = [int(num) for num in numbers]
    
    return numbers

def update_object(json_object):
     # If the input is a string, convert it to a dictionary
    if isinstance(json_object, str):
        try:
            json_object = json.loads(json_object)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return None  # or handle the error as needed

    # Now proceed assuming json_object is a dictionary
    if isinstance(json_object, dict):
        if 'containers' in json_object:
            for container in json_object.get('containers', []):
                for item in container.get('items', []):
                    if 'item' in item:
                        item['Item'] = remove_control_chars(item['item'])
                        item['Item'] = swap_number_string(item['Item'])
                        item['Item'] = extract_numbers(item['Item'])
                        del item['item']
                    if 'pkgs' in item:
                        item['Packages'] = remove_control_chars(item['pkgs'])
                        item['Packages'] = extract_numbers(item['pkgs'])
                        del item['pkgs']
                    if 'weight' in item:
                        item['Gross Weight'] = remove_control_chars(item['weight'])
                        item['Gross Weight'] = switch_number_and_string(item['Gross Weight'])
                        item['Gross Weight'] = extract_numbers(item['Gross Weight'])
                        del item['weight']
    
    return json_object

