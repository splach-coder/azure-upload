import re

# Mapping letters to their corresponding numeric values
LETTER_VALUES = {
    'A': 10, 'B': 12, 'C': 13, 'D': 14, 'E': 15, 'F': 16, 'G': 17, 'H': 18, 'I': 19,
    'J': 20, 'K': 21, 'L': 23, 'M': 24, 'N': 25, 'O': 26, 'P': 27, 'Q': 28, 'R': 29,
    'S': 30, 'T': 31, 'U': 32, 'V': 34, 'W': 35, 'X': 36, 'Y': 37, 'Z': 38
}

def calculate_check_digit(container_number):
    """Calculate the ISO 6346 check digit for a given container number."""
    # Weights corresponding to each position
    weights = [2**i for i in range(10)]
    
    total = 0
    for i, char in enumerate(container_number[:10]):
        if char.isdigit():
            value = int(char)
        else:
            value = LETTER_VALUES.get(char, 0)
        total += value * weights[i]
    
    remainder = total % 11
    return remainder if remainder < 10 else 0

def is_valid_container_number(container_number):
    """Validate the container number against ISO 6346 standards."""
    # Regular expression to match the format: 4 letters, 6 digits, 1 digit (check digit)
    if not re.match(r'^[A-Z]{4}\d{7}$', container_number):
        return False
    
    # Calculate the expected check digit
    expected_check_digit = calculate_check_digit(container_number)
    
    # Actual check digit is the last digit of the container number
    actual_check_digit = int(container_number[-1])
    
    return expected_check_digit == actual_check_digit

def string_to_unique_array(input_string):
    # Split the string by comma, strip spaces, and remove duplicates using a set
    return list(set(item.strip() for item in input_string.split(',')))