import re 
from bs4 import BeautifulSoup

from global_db.countries.functions import get_abbreviation_by_country

def clean_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()


def extract_email_data(email_html):
    try:
        # Parse HTML content to plain text
        soup = BeautifulSoup(email_html, "html.parser")
        plain_text = soup.get_text(separator="\n")  # Use separator to preserve line breaks

        # Regex patterns
        ci_pattern = r"CI\s*[\xa0\s]*(\d+)"  # Matches 'CI' followed by optional spaces/non-breaking spaces and numbers
        location_pattern = r"Locatie goederen\s*:\s*([^\s\n]+)"  # Matches 'Locatie goederen :' and captures location

        # Extract CI number
        ci_match = re.search(ci_pattern, plain_text)
        ci_number = f"CI {ci_match.group(1)}" if ci_match else None

        # Extract location
        location_match = re.search(location_pattern, plain_text)
        if location_match:
            location = location_match.group(1).strip()
            # Clean up the location (if extra spaces or unexpected text are present)
            location = re.sub(r"[^a-zA-Z\s]", "", location).strip()  # Remove non-alphabetical characters
        else:
            location = None

        # Return extracted data
        return {
            "Reference": ci_number,
            "Location": location
        }

    except Exception as e:
        return {"error": str(e)}  

def process_data(input_data):
    # Function to safely normalize numeric strings to floats
    def normalize_to_float(value):
        try:
            # Remove commas and other unwanted characters before converting to float
            return float(re.sub(r'[^\d.-]', '', value))
        except (ValueError, TypeError):
            return None

    # Convert relevant fields to floats
    input_data["Net weight Total"] = normalize_to_float(input_data.get("Net weight Total", "0"))
    input_data["Gross weight Total"] = normalize_to_float(input_data.get("Gross weight Total", "0"))
    input_data["Total"] = normalize_to_float(input_data.get("Total", "0"))
    input_data["Total Pallets"] = normalize_to_float(input_data.get("Total Pallets", "0"))

    # Process Incoterm field
    incoterm = input_data.get("Incoterm", "")
    # Remove special characters and split by the first space
    cleaned_incoterm = re.sub(r'[^\w\s]', '', incoterm).strip()
    input_data["Incoterm"] = cleaned_incoterm.split(' ', maxsplit=1)
    
    #abbr the country
    Country = input_data.get("Address", "")[0].get("Country")
    input_data["Address"][0]["Country"] = get_abbreviation_by_country(Country)

    return input_data
    
       
         