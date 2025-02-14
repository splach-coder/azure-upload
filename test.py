import re

def extract_postal_code(email_body):
    """
    Extract Belgian postal code from email signature.
    Looks for patterns like B-2220 or 2220 in address context.
    
    Args:
        email_body (str): Full email body text
    
    Returns:
        str: Extracted postal code (2220 or 2580) or None if not found
    """
    # Look for common Belgian postal code patterns
    patterns = [
        r'B-(\d{4})',  # Matches B-2220
        r'BE-(\d{4})',  # Matches BE-2220
        r'Belgium.*?(\d{4})',  # Matches postal code near "Belgium"
        r'(\d{4}).*?Belgium',  # Matches postal code before "Belgium"
        r'(\b2220\b|\b2580\b)'  # Specifically look for 2220 or 2580
    ]
    
    # Try each pattern
    for pattern in patterns:
        matches = re.finditer(pattern, email_body, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            code = match.group(1) if len(match.groups()) > 0 else match.group(0)
            # Only return if it's one of the expected codes
            if code in ['2220', '2580']:
                return code
    
    return None

def process_email_location(email_body):
    """
    Process email body and determine goods location based on postal code.
    
    Args:
        email_body (str): Full email body text
    
    Returns:
        dict: Result containing postal code and status
    """
    postal_code = extract_postal_code(email_body)
    
    return {
        'postal_code': postal_code,
        'found': postal_code is not None,
        'message': f"Found postal code: {postal_code}" if postal_code else "No valid postal code found"
    }

# Test with example email
example_email = """Beste,

 

Zouden jullie een exportdocument kunnen opstellen voor een zending naar UAE ajb?

 

Kantoor van uitgang is: BE212000

Vrachtkost: 50,- EUR

Aantal colli: 1

 

Regeling 10 00

 

Bijgevoegd onze factuur.

 

Alvast bedankt!

 

 

Best regards,

 

Sandra Henderickx

Customer Care - Traffic Assistant

 

Kito Crosby

Heist-op-den-Berg, Belgium

Office: (+32)(0)15768892

sandra.henderickx@kitocrosby.com

www.kitocrosby.com

 



 

Crosby Europe nv

Industriepark zone B nr. 26

2220 Heist-op-den-Berg

Monday-Thursday : 08h00 – 12h00 / 12h30 – 16h30

Friday : 08h00 – 12h00 / 12h30 – 15h30

 

 """

# Test the function
result = process_email_location(example_email)
print(result.get("found", ""))