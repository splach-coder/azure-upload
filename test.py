import re


data = [['421378', '421377', '421360', '421359', '421358', '224'], ['576 NR', '640 NR', '1OO NR', '80 NR', '80 NR', '52 NR'], ['481 81 01 0', "481810'10", '48182091', '48182091', '481 82091', '44152020'], ['g', 'g', '2.470,464', '2.060,800', '278,700', '150,000', '150,000', '1.404,000']]

def filter_numeric_strings(input_list):
    def is_number(s):
        s = s.strip()  # Remove leading/trailing whitespace
        # Exclude strings that are purely alphabetic (like 'g', 'abc')
        if re.fullmatch(r'[a-zA-Z]+', s):
            return False
        # Allow numbers, decimals, commas, and optional "NR"
        return True
    
    # Process the list of lists
    cleaned_list = []
    for sublist in input_list:
        filtered_sublist = [item for item in sublist if is_number(item)]
        cleaned_list.append(filtered_sublist)
    
    return cleaned_list

print(filter_numeric_strings(data))