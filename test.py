
def format_references(reference_str):
    # Extract and sort unique numbers
    refs = sorted(set(map(int, re.findall(r'\d+', reference_str))))  
    base = str(refs[0])[:-2]  # Take the base part of the first number
    formatted_refs = [str(refs[0])]

    for i in range(1, len(refs)):
        current = str(refs[i])
        prev = str(refs[i - 1])

        # Check if only the last two digits change (same base)
        if current[:-2] == prev[:-2]:
            formatted_refs.append(current[-2:])  # Add only last two digits
        else:
            formatted_refs.append("/" + current)  # Start a new base

    return base + "/".join(formatted_refs[1:])  # Join formatted parts