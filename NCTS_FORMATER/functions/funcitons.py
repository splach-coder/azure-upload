import json
import re

def replace_between_asterisks(input_string, replacement_value):
    """
    Replaces the value inside * * with a given parameter.
    
    :param input_string: str, the input string containing *value*.
    :param replacement_value: str, the value to replace inside * *.
    :return: str, modified string.
    """
    return re.sub(r'\*(.*?)\*', f'*{replacement_value}*', input_string, count=1)

def combine_jsons_one_to_many_relation(json_one, json_two):
    """
    Combines a single JSON object (json_one) with a list of JSON objects (json_two).

    :param json_one: dict, the first JSON with one item.
    :param json_two: list of dicts, the second JSON with two or more items.
    :return: list of combined JSON objects.
    """
    # Extract relevant fields from the first JSON
    item = 1
    arrival_notice1 = json_one["ArrivalNotice1"]
    arrival_notice2 = json_one["ArrivalNotice2"]
    container = json_one["container"]
    description = json_one["Description"]

    # Combine fields with each item in the second JSON
    combined_result = []
    for entry in json_two:
        combined_entry = {
            "item": item,
            "ArrivalNotice1": arrival_notice1,
            "ArrivalNotice2": replace_between_asterisks(arrival_notice2, item),
            "container": container,
            "Description": description,
            **entry  # Add the entire entry from json_two
        }
        combined_result.append(combined_entry)
        item = item+1

    return combined_result

def combine_jsons_many_to_one_relation(json_one, json_two):
    """
    Combines a list JSON objects (json_one) with a single of JSON object (json_two).

    :param json_one: dict, the first JSON with two or more items..
    :param json_two: list of dicts, the second JSON with one item.
    :return: list of combined JSON objects.
    """

    # Combine fields with each item in the second JSON
    combined_result = []
    for entry in json_one:
        combined_entry = {
            **json_two,
            **entry  # Add the entire entry from json_two
        }
        combined_result.append(combined_entry)

    return combined_result

def remove_fields_from_json(json_data, fields_to_remove):
    """
    Removes specified fields from a JSON object or list of JSON objects.

    :param json_data: dict or list of dicts, JSON data from which fields should be removed
    :param fields_to_remove: list of str, field names to remove
    :return: dict or list of dicts, JSON data with specified fields removed
    """
    if isinstance(json_data, dict):
        return {key: value for key, value in json_data.items() if key not in fields_to_remove}
    elif isinstance(json_data, list):
        return [remove_fields_from_json(item, fields_to_remove) for item in json_data]
    else:
        raise TypeError("Invalid JSON data type. Expected dict or list of dicts.")
    
def compare_numbers_with_tolerance(num1, num2, tolerance=5):
    """
    Compares two numbers and checks if the absolute difference is within the given tolerance.

    :param num1: float, the first number
    :param num2: float, the second number
    :param tolerance: float, the allowed absolute difference (default is 5)
    :return: bool, True if the difference is within tolerance, False otherwise
    """
    # Calculate the absolute difference
    absolute_difference = abs(num1 - num2)

    # Check if the absolute difference is within the tolerance
    return absolute_difference <= tolerance    