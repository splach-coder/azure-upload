from datetime import datetime
import requests
import xml.etree.ElementTree as ET


def fetch_exchange_rate(currency_code):
    # Get the current year and month in "YYYYMM" format
    current_date = datetime.now().strftime("%Y%m")

    # Insert the dynamic part into the URL
    url = f"https://www.belastingdienst.nl/data/douane_wisselkoersen/wks.douane.wisselkoersen.dd{current_date}.xml"
    print(f"Fetching exchange rate from URL: {url}")
    
    # Fetch XML content from the URL
    response = requests.get(url)
    
    if response.status_code == 200:
        # Parse XML content
        root = ET.fromstring(response.content)
        
        # Find the currency block that matches the currency code
        for rate in root.findall("douaneMaandwisselkoers"):
            code = rate.find("muntCode").text
            if code == currency_code:
                foreign_rate = rate.find("tariefInVreemdeValuta").text
                return foreign_rate
    
    return 0.0  # Return None if the currency was not found or request failed

# Example usage
if __name__ == "__main__":
    currency = "EUR"  # Example currency code
    exchange_rate = fetch_exchange_rate(currency)
    print(f"Exchange rate for {currency}: {exchange_rate}")
    