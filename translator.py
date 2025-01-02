import re

str = "FW: Export LCL Sea freight Egypt - Crosby ref KDR 15010 - Pickup: 06/01"
str1 = "FW: Export Road NORWAY - Certex Norge, Stavanger - Crosby ref SH 15029/999606972--979 - Pickup: Friday ~08h00"

def extract_reference(text):
    # Define the regex pattern to find the reference after "ref"
    pattern = r"ref\s+(\w+\s+\d+(?:/\d+)?)"
    
    # Search for the pattern in the text
    match = re.search(pattern, text)
    
    # Return the matched reference or None if not found
    return match.group(1) if match else None

print(extract_reference(str))

