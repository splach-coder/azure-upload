import re

def format_references(reference_str):
    # Extract and sort unique numbers
    refs = sorted(set(map(int, re.findall(r'\d+', reference_str))))  
    base = str(refs[0])[:-2]  # Take the base part of the first number
    formatted_refs = [str(refs[0])]  # Start with the full first reference

    for i in range(1, len(refs)):
        current = str(refs[i])
        prev = str(refs[i - 1])

        # Check if only the last two digits change (same base)
        if current[:-2] == prev[:-2]:
            formatted_refs.append(current[-2:])  # Add only last two digits
        else:
            formatted_refs.append("/" + current)  # Start a new base

    return "/".join(formatted_refs)  # Join formatted parts

text = '3000621614+3000621619+3000621615+3000621618'
print(format_references(text))