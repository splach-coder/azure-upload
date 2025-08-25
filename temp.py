import re

def parse_weight(number_str: str) -> str:
    """
    Normalizes a weight string from an invoice to a standard format (e.g., '1234.565').

    This function is designed based on the rule that weights always have three decimal places.
    It intelligently detects the decimal separator (',' or '.') based on this rule.

    Args:
        number_str: The number string to parse, e.g., "1.234,565" or "1,234.565".

    Returns:
        A cleaned string in the standard 'INTEGER.DECIMAL' format.

    Raises:
        ValueError: If the number format is ambiguous or unrecognized.
    """
    if not isinstance(number_str, str):
        raise TypeError("Input must be a string.")

    s = number_str.strip()

    # If the last character is a comma or dot, it might be a dangling separator.
    if s.endswith(',') or s.endswith('.'):
        s = s[:-1]
        
    # Find the last occurrence of a comma and a dot
    last_comma_index = s.rfind(',')
    last_dot_index = s.rfind('.')

    # Case 1: The last separator is a comma, followed by exactly 3 digits.
    # This strongly indicates the EU format (e.g., "1.234,565" or "0,156").
    if last_comma_index > last_dot_index and len(s) - last_comma_index - 1 == 3:
        # Remove all dots (as thousands separators) and replace the comma with a dot.
        return s.replace('.', '').replace(',', '.')

    # Case 2: The last separator is a dot, followed by exactly 3 digits.
    # This strongly indicates the EN format (e.g., "1,234.565" or "0.635").
    if last_dot_index > last_comma_index and len(s) - last_dot_index - 1 == 3:
        # Remove all commas (as thousands separators).
        return s.replace(',', '')

    # Case 3: The number has no separators or they are not followed by 3 digits.
    # Treat it as an integer and remove all separators.
    cleaned_s = s.replace(',', '').replace('.', '')
    if cleaned_s.isdigit():
        return cleaned_s

    # If none of the above rules apply, the format is unrecognized.
    raise ValueError(f"Unrecognized or ambiguous number format: '{number_str}'")


print(parse_weight("0,350 "))