import re


text = """Doc N°.:90064108
ARTE NV
Company registration number: 0421.929.907
VAT number: BE 0421.929.907
RPR - RPM: Hasselt
General conditions of sale: www.arte-
international.com
Contact Details
t +32 11 81 93 10
sales.export@arte-international.com
www.arte-international.com
Banking Details
KBC IBAN: BE90 4547 0677 7132
BIC/SWIFT: KREDBEBB
BNP PARIBAS FORTIS IBAN: BE19 2350 3201 9712
BIC/SWIFT: GEBABEBB
2 / 2
Bank transfer (in)
Method of payment:
Please mention on payment: 90064108
Exempt TVA - article 39, § 1, 2° of the Belgian VAT code
The exporter of the products covered by this document  (customs authorisation Nº BE1048) declares that,
except where otherwise clearly indicated, these products are of EU preferential origin  according to the rules of
origin of the Generalized System of Preferences of the European Union. An Adriaensens,
Zonhoven,23.05.2025 An Adriaensens
2 PARCELS"""

def extract_customs_authorization_no(text):
    match = re.search(r"customs authori[sz]ation (?:No|Nº)\s*([A-Z0-9]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


if __name__ == "__main__":
    customs_no = extract_customs_authorization_no(text)
    print(f"Customs Authorization Number: {customs_no}")
    if customs_no:
        print(f"Customs No: {customs_no.upper()}")
    else:
        print("Customs authorization number not found.")
