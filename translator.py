from bs4 import BeautifulSoup
import re

def extract_freight_and_exit_office_from_html(html):
    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract all text from the HTML
    text = soup.get_text(separator=' ')
    
    # Regex for freight (amount followed by €)
    freight_pattern = r"(\d+(?:[.,]\d+)?\s?€)"
    
    # Regex for exit office (2 letters followed by 6 digits)
    exit_office_pattern = r"\b[A-Z]{2}\d{6}\b"
    
    # Search for freight
    freight_match = re.search(freight_pattern, text)
    freight = freight_match.group(1) if freight_match else None
    
    # Search for exit office
    exit_office_match = re.search(exit_office_pattern, text)
    exit_office = exit_office_match.group(0) if exit_office_match else None
    
    return {
        "freight": freight,
        "exit_office": exit_office
    }

# Example usage
html_email = """
<html>
<head></head>
<body>
<p>Hallo,</p>
<p>Kan u een exportdocument opmaken voor de bijgevoegde factuur?</p>
<p>Export via: <b>SE060340</b></p>
<p>Container#:</p>
<p>Transportkost tot EU-grens: <span>250€</span></p>
<p>Tenneco Warehouse will be closed for Christmas holidays from 23/12/2024 till 01/01/2025.</p>
<p>Kind regards - Met vriendelijke groeten</p>
<p>Diane Claes</p>
<p>Logistics Specialist</p>
<p>Tel: 0032/11703457</p>
<p>Tel counter : 0032/11 703177</p>
<p>diane.claes@driv.com</p>
</body>
</html>
"""

result = extract_freight_and_exit_office_from_html(html_email)
print(result)
