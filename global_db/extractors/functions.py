import re

def extract_Exitoffice(text):
    """
    Extract the container number from a given text.
    The format is: Two characters (letters), optional space, four numbers.
    
    Args:
        text (str): The input text.
    
    Returns:
        str or None: The container number if found, otherwise None.
    """
    pattern = r"\b([A-Za-z]{2}\s?\d{6})\b"
    match = re.search(pattern, text)
    return match.group(1) if match else ""
