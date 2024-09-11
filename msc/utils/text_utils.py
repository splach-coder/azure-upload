import json
import re

def data_to_json(data_list, key_map):
    if len(data_list) != len(key_map):
        raise ValueError("Length of data list and key map must be equal.")

    data_dict = dict(zip(key_map, data_list))
    return json.dumps(data_dict)

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

def update_object(json_object, object_key):
    for key in json_object:
        if key == object_key and key == "Gross Weight":
            json_object[key] = remove_control_chars(json_object[key])
            json_object[key] = switch_number_and_string(json_object[key])
        if key == object_key and key == "Packages":
            json_object[key] = remove_control_chars(json_object[key])
        if key == object_key and key == "Item":
            json_object[key] = remove_control_chars(json_object[key])
            json_object[key] = swap_number_string(json_object[key])
    return json_object

