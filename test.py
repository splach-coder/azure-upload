import requests
import json
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from AI_agents.Gemeni.functions.functions import convert_to_list, query_gemini
from bs4 import BeautifulSoup
import re

class AddressParser:
    def __init__(self, key_vault_url="https://kv-functions-python.vault.azure.net", secret_name="Gemeni-api-key"):
        """
        Initialize the AddressParser with the Azure Key Vault configuration.
        
        Args:
            key_vault_url (str): URL of the Azure Key Vault
            secret_name (str): Name of the secret containing the Gemini API key
        """
        self.key_vault_url = key_vault_url
        self.secret_name = secret_name
        self.api_key = None
        
    def initialize_api_key(self):
        """
        Retrieve the Gemini API key from Azure Key Vault.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Use DefaultAzureCredential for authentication
            credential = DefaultAzureCredential()
            # Create a SecretClient to interact with the Key Vault
            client = SecretClient(vault_url=self.key_vault_url, credential=credential)
            # Retrieve the secret value
            self.api_key = client.get_secret(self.secret_name).value
            return True
        except Exception as e:
            logging.error(f"Failed to retrieve secret: {str(e)}")
            return False
        
    def search_for_location(self, email_body: str) -> str:
        """Searches for 'Wijnegem' or 'Maasmechelen' in the email body and returns the found word."""
        # Define the keywords to search for (case-insensitive)
        keywords = ["Wijnegem", "Maasmechelen"]

        # Search for keywords in the entire email body
        for keyword in keywords:
            if re.search(rf'\b{keyword}\b', email_body, re.IGNORECASE):
                return keyword.capitalize()

        # Return an empty string if none found
        return ""    
        
    def extract_email_body(self, html_content: str) -> str:
        """Extracts and cleans the main body text from an HTML email."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove unnecessary elements like scripts, styles, and hidden elements
            for tag in soup(['script', 'style', 'head', 'meta', 'link', 'title', '[hidden]']):
                tag.decompose()

            # Extract visible text only
            body_text = soup.get_text(separator='\n', strip=True)

            # Remove excessive whitespace and clean the text
            cleaned_text = '\n'.join(line.strip() for line in body_text.splitlines() if line.strip())

            return cleaned_text

        except Exception as e:
            print(f"Error while extracting email body: {e}")
            return ""    
            
    def parse_address(self, address):
        """
        Parse an address string into structured components using Gemini API.
        
        Args:
            address (str): The address to parse
            
        Returns:
            list: Parsed address components [company, street, city, postal_code, country_code]
                  or None if parsing failed
        """
        if not self.api_key and not self.initialize_api_key():
            logging.error("No API key available")
            return None
            
        prompt = f"""Extract the following information from the provided email:

            Collis: The number of collis as a string.
            Weight: The weight as a float, with all formatting cleaned (e.g., "5,610kg" → "5610").
            Exit Office: The exit office code in the format of two letters followed by six numbers (e.g., "FR002300").
            If any field is missing, return an empty string for it.
            Return the result as a Python dictionary with all values as strings.
            Provide only the JSON-like output with no additional text or formatting no json text.

            extract data from here:

            [{address}]"""
        
        try:
            result = query_gemini(self.api_key, prompt)
            result = result.get("candidates")[0].get("content").get("parts")[0].get("text")
            #parsed_address = convert_to_list(result)
            return result
        except requests.exceptions.RequestException as e:
            logging.error(f"Error making request: {e}")
            return None
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing response: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error during address parsing: {e}")
            return None

# Example usage
if __name__ == "__main__":
    parser = AddressParser()
    email = """<html><head>\r\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"><style type=\"text/css\" style=\"display:none\">\r\n<!--\r\np\r\n\t{margin-top:0;\r\n\tmargin-bottom:0}\r\n-->\r\n</style></head><body dir=\"ltr\"><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:11pt; color:rgb(36,36,36)\">Beste</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:11pt; color:rgb(36,36,36)\">&nbsp;</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:11pt; color:rgb(36,36,36)\">Graag 1 EU A document op te willen maken voor CI 1165586</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:11pt; color:rgb(36,36,36)\">&nbsp;</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:11pt; color:rgb(36,36,36)\">1 PAL // 107,42 KG</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:11pt; color:rgb(36,36,36)\">Locatie goederen : Wijnegem</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:11pt; color:rgb(36,36,36)\">HS code&nbsp; : see enclosed document</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:11pt; color:rgb(36,36,36)\">Origin of goods : see enclosed document</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:11pt; color:rgb(36,36,36)\">Incoterms : CIP</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:11pt; color:rgb(36,36,36)\">Waarde goederen : € 3.815,58</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Arial,sans-serif,serif,EmojiFont; font-size:11pt; color:rgb(0,159,130)\"><b>&nbsp;</b></span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:11pt; color:rgb(36,36,36)\"><b>Met vriendelijke groeten, mit freundlichen Grüssen, with kind regards,</b></span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:11pt; color:rgb(36,36,36)\">&nbsp;</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:11pt; color:rgb(53,53,53)\">Christof VERHELST</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:8pt; color:rgb(68,68,68)\">Expediteur Import/Export UK</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:6pt; color:rgb(36,36,36)\">&nbsp;</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:&quot;Segoe UI Emoji&quot;,sans-serif,serif,EmojiFont; font-size:10pt; color:rgb(36,36,36)\">📞</span><span style=\"font-family:Calibri,sans-serif; font-size:10pt; color:rgb(36,36,36)\">&nbsp;+32 50 81 60 04 | </span><span style=\"font-family:&quot;Segoe UI Emoji&quot;,sans-serif,serif,EmojiFont; font-size:10pt; color:rgb(36,36,36)\">☎️</span><span style=\"font-family:Calibri,sans-serif; font-size:10pt; color:rgb(36,36,36)\">&nbsp;+32 50 81 60 06 (ext. 512) | </span><span style=\"font-family:&quot;Segoe UI Emoji&quot;,sans-serif,serif,EmojiFont; font-size:10pt; color:black; background-color:white\">🌐</span><span style=\"font-family:Calibri,sans-serif; font-size:10pt; color:black; background-color:white\">&nbsp;</span><span style=\"font-family:Calibri,sans-serif; font-size:10pt; color:rgb(0,0,0)\"><a href=\"https://eur01.safelinks.protection.outlook.com/?url=http%3A%2F%2Fwww.cgeerts.be%2F&amp;data=05%7C02%7Cfoldermill%40dkm-customs.com%7C397dbddbd2bd435dcddb08dd580bb7eb%7Ca696cf459e704909a6742391335b26a9%7C0%7C0%7C638763529674497843%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&amp;sdata=K7IY%2F3Sz9c2mYrTswVExXwOgRqC0jrAfuTmr2TBuI1c%3D&amp;reserved=0\" originalsrc=\"http://www.cgeerts.be/\" target=\"_blank\" id=\"OWAe490a397-49ee-b915-f299-7123e9e79ac6\" class=\"OWAAutoLink\" title=\"Original URL: http://www.cgeerts.be/. Click or tap if you trust this link.\" rel=\"noopener noreferrer\" originalsrc=\"http://www.cgeerts.be/\" data-linkindex=\"0\" data-auth=\"NotApplicable\" style=\"color:rgb(0,0,0); margin:0px\">www.cgeerts.be</a></span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:&quot;Segoe UI Emoji&quot;,sans-serif,serif,EmojiFont; font-size:10pt; color:black\">📧</span><span style=\"font-family:Calibri,sans-serif; font-size:10pt; color:black\">&nbsp;</span><span style=\"font-family:Calibri,sans-serif; font-size:10pt; color:rgb(5,99,193)\"><u><a href=\"mailto:export.uk@geertstransport.com\" id=\"OWA5850dbb7-c55a-db63-544b-b2032b7d97e5\" class=\"OWAAutoLink\" title=\"mailto:export.uk@geertstransport.com\" data-linkindex=\"1\" style=\"color:rgb(5,99,193); margin:0px\">export.uk@geertstransport.com</a></u></span><span style=\"font-family:Calibri,sans-serif; font-size:10pt; color:black\">&nbsp;| </span><span style=\"font-family:Calibri,sans-serif; font-size:10pt; color:rgb(36,36,36)\">ISO 9001-2015</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:6pt; color:rgb(36,36,36)\">&nbsp;</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:12pt; color:rgb(36,36,36)\"><img id=\"x_Afbeelding_x0020_1707867875\" width=\"626\" height=\"144\" size=\"194728\" data-outlook-trace=\"F:1|T:1\" src=\"cid:db6010c0-18c3-42d4-8adf-745e89075a82\" style=\"width:6.5312in; height:1.5104in; max-width:947px; min-width:auto; min-height:auto; margin:0px\"></span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:6pt; color:rgb(36,36,36)\">&nbsp;</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:8pt; color:rgb(0,0,0)\"><b><a href=\"https://eur01.safelinks.protection.outlook.com/?url=https%3A%2F%2Fifa-forwarding.net%2F&amp;data=05%7C02%7Cfoldermill%40dkm-customs.com%7C397dbddbd2bd435dcddb08dd580bb7eb%7Ca696cf459e704909a6742391335b26a9%7C0%7C0%7C638763529674521027%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&amp;sdata=zEUdZHUH5RHTWFGaegs%2Bo%2Bpb%2F%2FqIoxo4jFbmG7kvew0%3D&amp;reserved=0\" originalsrc=\"https://ifa-forwarding.net/\" target=\"_blank\" id=\"OWA6192a6e2-c34d-805f-fcb7-62573cf47ba5\" class=\"OWAAutoLink\" title=\"Original URL: https://ifa-forwarding.net/. Click or tap if you trust this link.\" rel=\"noopener noreferrer\" originalsrc=\"https://ifa-forwarding.net/\" data-linkindex=\"2\" data-auth=\"NotApplicable\" style=\"color:rgb(0,0,0); margin:0px\">Member of:&nbsp;INTERNATIONAL FORWARDING ASSOCIATION&nbsp;…&nbsp;we care for your cargo</a></b></span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:6.5pt; color:red\"><u><a href=\"https://eur01.safelinks.protection.outlook.com/?url=https%3A%2F%2Fcgeerts.be%2Fwp-content%2Fuploads%2F2024%2F02%2FGENERAL-CONDITIONS-2024.pdf&amp;data=05%7C02%7Cfoldermill%40dkm-customs.com%7C397dbddbd2bd435dcddb08dd580bb7eb%7Ca696cf459e704909a6742391335b26a9%7C0%7C0%7C638763529674533489%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&amp;sdata=V6VZE5Aphz6li3%2BgYBOLVSXHTkrK%2Ffe%2BidsQ28hPZXk%3D&amp;reserved=0\" originalsrc=\"https://cgeerts.be/wp-content/uploads/2024/02/GENERAL-CONDITIONS-2024.pdf\" target=\"_blank\" id=\"OWA9bec7577-a92d-adea-ebfa-3dc3ed331ada\" class=\"OWAAutoLink\" title=\"Original URL: https://cgeerts.be/wp-content/uploads/2024/02/GENERAL-CONDITIONS-2024.pdf. Click or tap if you trust this link.\" rel=\"noopener noreferrer\" originalsrc=\"https://cgeerts.be/wp-content/uploads/2024/02/GENERAL-CONDITIONS-2024.pdf\" data-linkindex=\"3\" data-auth=\"NotApplicable\" style=\"color:red; margin:0px\">Our General Terms and Conditions shall invariably apply to all of our accepted assignments and all of our activities.</a></u></span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:6.5pt; color:rgb(123,123,123)\">Our General Terms and Conditions may be consulted online at your convenience on <u><a href=\"https://eur01.safelinks.protection.outlook.com/?url=http%3A%2F%2Fwww.cgeerts.be%2F&amp;data=05%7C02%7Cfoldermill%40dkm-customs.com%7C397dbddbd2bd435dcddb08dd580bb7eb%7Ca696cf459e704909a6742391335b26a9%7C0%7C0%7C638763529674545387%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&amp;sdata=knqDRrO9Zy5hfJgnK%2B7GVNMuHzad8yRUHT0zxrociWA%3D&amp;reserved=0\" originalsrc=\"http://www.cgeerts.be/\" target=\"_blank\" id=\"OWA0a723e65-d8f3-2bff-1eee-12298ab2f99b\" class=\"OWAAutoLink\" title=\"Original URL: http://www.cgeerts.be/. Click or tap if you trust this link.\" rel=\"noopener noreferrer\" originalsrc=\"http://www.cgeerts.be/\" data-linkindex=\"4\" data-auth=\"NotApplicable\" style=\"color:rgb(123,123,123); margin:0px\">www.cgeerts.be</a></u>. For matters concerning invoicing and</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:6.5pt; color:rgb(123,123,123)\">payment – indemnification clauses and arrears interests - liability restrictions - retention rights - applicable law - choice of forum,</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Calibri,sans-serif; font-size:6.5pt; color:rgb(123,123,123)\">we refer to our General Terms and Conditions.</span></p><p class=\"elementToProof\" style=\"text-align:left; text-indent:0px; background-color:rgb(255,255,255); margin:0cm\"><span style=\"font-family:Arial,sans-serif,serif,EmojiFont; font-size:7pt; color:rgb(0,159,130)\"><b><img id=\"x_Picture_x0020_13\" width=\"19\" height=\"19\" size=\"747\" data-outlook-trace=\"F:1|T:1\" src=\"cid:ebd49306-3d49-42de-b791-36fdae1aa7e9\" style=\"width:0.2083in; height:0.2083in; max-width:947px; min-width:auto; min-height:auto; margin:0px\">Please consider the environment before printing this document</b></span></p><div class=\"elementToProof\" style=\"font-family:Aptos,Aptos_EmbeddedFont,Aptos_MSFontService,Calibri,Helvetica,sans-serif; font-size:12pt; color:rgb(0,0,0)\"><br></div></body></html>"""
    parsed_result = parser.extract_email_body(email)
    goodsLocation = parser.search_for_location(email)
    parsed_result = parser.parse_address(email)
    parsed_result = parsed_result.replace('json', '').replace('```', '').strip()
    parsed_result = convert_to_list(parsed_result)
    parsed_result["GoodsLocation"] = goodsLocation

    print(parsed_result)
