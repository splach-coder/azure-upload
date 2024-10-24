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

# Function to detect country
def detect_country(address):
    for country in countries:
        # Check if the country is found in the address (case-insensitive)
        if country.lower() in address.lower():
            # Find the starting index of the country in the address
            start_index = address.lower().index(country.lower())
            # Find the ending index by adding the length of the country
            end_index = start_index + len(country)
            # Return the exact substring from the address
            return address[start_index:end_index].strip()  # Trim any extra spaces
    return None

# Function to detect postal code
def detect_postal_code(address):
    for pattern in postal_code_patterns:
        match = re.search(pattern, address)
        if match:
            return match.group(0)
    return None

# Function to extract company name heuristically
def extract_company_name(address):
    if ',' in address:
        return address.split(',')[0].strip()
    return ' '.join(address.split()[:2]).strip()

# Custom parsing rules for address components
def extract_address_components(address):
    company_name = extract_company_name(address) if extract_company_name(address) else ""
    street = None
    city = None
    postal_code = detect_postal_code(address)
    country = detect_country(address)

    # Remove company name and postal code from the address for further processing
    address_without_company = address.replace(company_name, "").replace(postal_code if postal_code else "", "").strip()

    # Remove company name and postal code from the address for further processing
    address_without_company = address_without_company.replace(country if country else "", "")

    # Split the remaining address into parts using commas or multiple spaces
    middle_adress = address_without_company.strip().split(' ')

    city = middle_adress[-1]
    street = ' '.join(middle_adress[:-1])

    return [company_name.strip(), street.strip(' .,') if street else None, city.strip() if city else None, postal_code.strip() if postal_code else None, country.strip() if country else None]
