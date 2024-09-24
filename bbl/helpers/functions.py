import re
import json

from bbl.helpers.searchOnPorts import search_ports

def process_container_data(data):
    data = data[0]

    # Validate the container format
    container = data.get("container", "")
    valid_container = extract_valid_container(container)

    if not valid_container:
        return # Skip entries without valid containers

    # Process Incoterm
    incoterm = data.get("Incoterm", "")
    incoterm_array = incoterm.split()  # Split into an array of strings

    # Process Freight
    freight = extract_numeric_value(data.get("Freight", "0 USD"))

    # Process Vat 1 and Vat 2
    vat1 = extract_numeric_value(data.get("Vat 1", "0 USD"))
    vat2 = sum(extract_numeric_value(vat) for vat in data.get("Vat 2", "0 EUR").split("+"))

    # Initialize totals
    total_gross_weight = 0.0
    total_net_weight = 0.0
    total_packages = 0.0
    total_devises = 0.0

    # Process items and calculate totals
    items = data.get("items", [])
    for item in items:
        total_gross_weight += extract_numeric_value(item.get("Gross Weight", "0"))
        total_net_weight += extract_numeric_value(item.get("Net Weight", "0"))
        total_packages += extract_numeric_value(item.get("Packages", "0"))
        total_devises += extract_numeric_value(item.get("VALEUR", "0"))  # Assuming VALEUR is in devises

    final_freight, final_vat = calculationVATndFREIGHT(total_devises, freight, vat1, vat2)

    dispatch_country = search_ports(incoterm_array[1])

    # Reconstruct the processed entry
    processed_entry = {
        "container": valid_container,
        "dispatch_country": dispatch_country,
        "Incoterm": incoterm_array,
        "Freight": round(final_freight, 2),
        "Vat": round(final_vat, 2),
        "items": items,
        "totals": {
            "Gross Weight": total_gross_weight,
            "Net Weight": total_net_weight,
            "Packages": total_packages,
            "DEVISES": total_devises
        }
    }

    return processed_entry

def extract_valid_container(container_string):
    container_arr = container_string.split(" ")
    container = None
    for str in container_arr:
        # Check if the container matches the format 4 chars and 7 digits
        pattern = r'^[A-Z]{4}\d{7}$'
        if re.match(pattern, str):
            container =  str

    return container

def extract_numeric_value(value):
    # Extract numeric value from string and convert to float
    match = re.search(r'[\d,.]+', value)
    if match:
        return float(match.group(0).replace(',', '.'))  # Replace comma with dot for float conversion
    return 0.0

def calculationVATndFREIGHT(price, freightUSD, vat1, vat2):
    EXCHANGE_RATE = 1.1116

    insurance = price * 0.3/100
    freightEUR = (freightUSD / EXCHANGE_RATE) + insurance

    vatEUR = vat1 / EXCHANGE_RATE + vat2

    return [freightEUR, vatEUR]
