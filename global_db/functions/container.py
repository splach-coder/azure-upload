import re


def is_valid_container_number(s):
    # Regular expression to match 4 characters followed by 7 digits
    pattern = r'^[A-Za-z]{4}\d{7}$'

    if s is None:
        return False
    
    # Use re.match to check if the string matches the pattern
    if re.match(pattern, s):
        return True
    else:
        return False


def is_valid_quay_number(s):
    # Regular expression to match 'K' followed by up to 4 digits
    pattern = r'^K\d{1,4}$'
    
    # Use re.match to check if the string matches the pattern
    if re.match(pattern, s):
        return True
    else:
        return False