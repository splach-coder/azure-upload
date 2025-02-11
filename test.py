test = {
"Aanvraag export 5568356 op vergunde parking" : 5568356,
"Aanvraag export 5568357 op vergunde parking": 5568357,
"EXPORT SOFIDEL 5564290": 5564290,
"Aanvraag export 5568356 op vergunde parking": 5568356,
"Aanvraag export 5568357 op vergunde parking": 5568357,
"EXPANT*29052 AAvraag export 5565759": 5565759,
"Aanvraag export 5568313 op vergunde parking": 5568313,
"EXPANT*28630  Aanvraag export 5567165 op vergunde parking": 5567165,
"EXPANT*28631  Aanvraag export 5567166 op vergunde parking": 5567166,
"EXPANT*28182 EXPORT SOFIDEL 5564355": 5564355,
"EXPANT*28167 REQUEST EXPORT SOFIDEL 5565758 OP VERGUNDE PARKING": 5565758,
"EXPORT SOFIDEL 5564290": 5564290,
"REQUEST EXPORT SOFIDEL 5564425 OP VERGUNDE PARKING": 5564425,
"EXPORT SOFIDEL 5564404": 5564404,
"EXPANT*27723  EXPORT SOFIDEL 5561684": 5561684,
"EXPANT*27722  REQUEST EXPORT SOFIDEL 5564362 OP VERGUNDE PARKING": 5564362,
"REQUEST EXPORT SOFIDEL 5563101": 5563101
}

import re

def extract_id_from_string(input_string):
    # Use a regular expression to find a 7-digit number in the string
    match = re.search(r'\d{7}', input_string)
    if match:
        # Return the ID as an integer
        return int(match.group())
    else:
        # Return None if no ID is found
        return None

# Example usage
for input_string, value in test.items():
    id = extract_id_from_string(input_string)
    print(id)