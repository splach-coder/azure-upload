import re

# List of countries (shortened example, add more countries as needed)
countries = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", 
    "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", 
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", 
    "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo", "Congo (Democratic Republic)", 
    "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "East Timor", 
    "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", 
    "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", 
    "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", 
    "Ireland", "Israel", "Italy", "Ivory Coast", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", 
    "Korea (North)", "Korea (South)", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", 
    "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", 
    "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", 
    "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Macedonia", 
    "Norway", "Oman", "Pakistan", "Palau", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", 
    "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", 
    "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", 
    "Somalia", "South Africa", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Zwitserland", "Syria", 
    "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", 
    "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", 
    "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]

postal_code_patterns = [
    # US-style ZIP codes (5 digits, optionally followed by a dash and 4 digits)
    r'\b\d{5}(?:-\d{4})?\b',  # e.g., 12345 or 12345-6789

    # Canada (postal codes are in the format: A1A 1A1)
    r'\b[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d\b',  # e.g., K1A 0B1 or K1A-0B1

    # UK (various formats such as SW1A 1AA, M1 1AA, etc.)
    r'\b[A-Za-z]{1,2}\d[A-Za-z\d]?[ ]?\d[A-Za-z]{2}\b',  # e.g., SW1A 1AA, M1 1AA

    # Japan (postal code in the format 123-4567)
    r'\b\d{3}-\d{4}\b',  # e.g., 123-4567

    # Germany (5-digit postal code)
    r'\b\d{5}\b',  # e.g., 12345

    # France (5-digit postal code)
    r'\b\d{5}\b',  # e.g., 75008

    # Switzerland (4-digit postal code)
    r'\b\d{4}\b',  # e.g., 8000

    # Italy (5-digit postal code)
    r'\b\d{5}\b',  # e.g., 00100

    # Netherlands (postal codes are 4 digits followed by two uppercase letters)
    r'\b\d{4}[ ]?[A-Z]{2}\b',  # e.g., 1234 AB

    # Australia (4-digit postal code)
    r'\b\d{4}\b',  # e.g., 4000

    # Spain (5-digit postal code)
    r'\b\d{5}\b',  # e.g., 28001

    # Brazil (postal code in the format 12345-678)
    r'\b\d{5}-\d{3}\b',  # e.g., 12345-678

    # Belgium (4-digit postal code)
    r'\b\d{4}\b',  # e.g., 1000

    # Argentina (postal codes can be alphanumeric in the format A1234AAA)
    r'\b[A-Z]\d{4}[A-Z]{3}\b',  # e.g., B1636ABC

    # Mexico (5-digit postal code)
    r'\b\d{5}\b',  # e.g., 12345

    # Russia (6-digit postal code)
    r'\b\d{6}\b',  # e.g., 123456

    # China (6-digit postal code)
    r'\b\d{6}\b',  # e.g., 100000

    # India (6-digit postal code)
    r'\b\d{6}\b',  # e.g., 110001

    # South Africa (4-digit postal code)
    r'\b\d{4}\b',  # e.g., 8001

    # Sweden (postal code in the format 123 45)
    r'\b\d{3}[ ]?\d{2}\b',  # e.g., 123 45 or 12345

    # Norway (4-digit postal code)
    r'\b\d{4}\b',  # e.g., 5000

    # Denmark (4-digit postal code)
    r'\b\d{4}\b',  # e.g., 1050

    # Finland (5-digit postal code)
    r'\b\d{5}\b',  # e.g., 00100

    # Poland (postal code in the format 12-345)
    r'\b\d{2}-\d{3}\b',  # e.g., 00-950

    # Portugal (postal code in the format 1234-567)
    r'\b\d{4}-\d{3}\b',  # e.g., 1234-567

    # Austria (4-digit postal code)
    r'\b\d{4}\b',  # e.g., 1010

    # Hungary (4-digit postal code)
    r'\b\d{4}\b',  # e.g., 1051

    # Greece (5-digit postal code)
    r'\b\d{5}\b',  # e.g., 10552

    # Romania (6-digit postal code)
    r'\b\d{6}\b',  # e.g., 010011

    # Turkey (5-digit postal code)
    r'\b\d{5}\b',  # e.g., 34000

    # South Korea (postal code in the format 123-456)
    r'\b\d{3}-\d{3}\b',  # e.g., 123-456

    # Israel (7-digit postal code)
    r'\b\d{7}\b',  # e.g., 6100000
]

# Function to detect postal code
def detect_postal_code(address):
    """
    Detect and return the postal code from a given address.
    
    Parameters:
    address (str or list[str]): The address or list of address strings to search.
    
    Returns:
    str or None: The detected postal code, or None if not found.
    """
    # Ensure address is a list
    if isinstance(address, str):
        address = [address]
    
    # Iterate through the address list in reverse order
    for addr in reversed(address):
        for pattern in postal_code_patterns:
            match = re.search(pattern, addr)
            if match:
                return match.group(0)
    
    # If no postal code found, return None
    return None

# Function to extract a specific section by its title
def extract_specific_section(text, section_title):
    # Split by lines of underscores
    sections = re.split(r'_{2,}', text)
    
    # Iterate through each section to find the one that starts with the title
    for section in sections:
        lines = section.strip().splitlines()
        if lines and lines[0].strip() == section_title:
            # Return the section title and its content
            content = "\n".join(lines[1:]).strip()
            return f"{section_title}:\n{content}".split('\n')[2:]

    return f"{section_title} section not found."

def get_adress_structure(text):
    arr = extract_specific_section(text, "BTW-nummer")

    company_name = arr[0]
    street_name = arr[1]
    code_postal = detect_postal_code(arr)
    city = arr[2].replace(code_postal, "") if code_postal is not None else arr[2]
    country = arr[-1].replace("Ver.", "").strip()

    return [company_name, street_name, city, code_postal, country]