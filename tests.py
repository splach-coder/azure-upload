import re
from bs4 import BeautifulSoup

# Regex patterns for 'Exit office' and 'Kantoor'
exit_office_pattern = r"Exit\s+office[:;]?\s*(BE?\d{5,8})"
kantoor_pattern = r"Kantoor[:;]?\s*(B?E?\d{5,8})"

def extract_body_text(html_content):
    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Extract text from the body tag, if it exists
    if soup.body:
        body_text = soup.body.get_text(separator="\n").strip()
        return body_text
    else:
        return "No body tag found."

# Function to extract the values
def extract_office_value(text):
    # Search for 'Exit office'
    exit_office_match = re.search(exit_office_pattern, text, re.IGNORECASE)
    if exit_office_match:
        return exit_office_match.group(1)
    
    # Search for 'Kantoor'
    kantoor_match = re.search(kantoor_pattern, text, re.IGNORECASE)
    if kantoor_match:
        return kantoor_match.group(1)
    
    return None

text = "<html><head>\r\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"><meta name=\"Generator\" content=\"Microsoft Word 15 (filtered medium)\"><style>\r\n<!--\r\n@font-face\r\n\t{font-family:\"Cambria Math\"}\r\n@font-face\r\n\t{font-family:Calibri}\r\n@font-face\r\n\t{font-family:Verdana}\r\n@font-face\r\n\t{font-family:Aptos}\r\n@font-face\r\n\t{font-family:\"Agency FB\"}\r\np.MsoNormal, li.MsoNormal, div.MsoNormal\r\n\t{margin:0in;\r\n\tfont-size:12.0pt;\r\n\tfont-family:\"Aptos\",sans-serif}\r\np.MsoPlainText, li.MsoPlainText, div.MsoPlainText\r\n\t{margin:0in;\r\n\tfont-size:11.0pt;\r\n\tfont-family:\"Calibri\",sans-serif}\r\nspan.EmailStyle17\r\n\t{font-family:\"Aptos\",sans-serif;\r\n\tcolor:windowtext}\r\nspan.PlainTextChar\r\n\t{font-family:\"Calibri\",sans-serif}\r\n.MsoChpDefault\r\n\t{}\r\n@page WordSection1\r\n\t{margin:1.0in 1.0in 1.0in 1.0in}\r\ndiv.WordSection1\r\n\t{}\r\n-->\r\n</style></head><body lang=\"EN-US\" link=\"#467886\" vlink=\"#96607D\" style=\"word-wrap:break-word\"><div class=\"WordSection1\"><p class=\"MsoPlainText\"><span lang=\"NL-BE\">Beste klant,</span></p><p class=\"MsoPlainText\"><span lang=\"NL-BE\">&nbsp;</span></p><p class=\"MsoPlainText\"><span lang=\"NL-BE\">Gelieve in bijlage u document(en) te vinden.</span></p><p class=\"MsoPlainText\"><span lang=\"NL-BE\">kantoor: 212000</span></p><p class=\"MsoPlainText\"><span lang=\"NL-BE\">Vriendelijke groeten,</span></p><p class=\"MsoNormal\"><span lang=\"NL-BE\">&nbsp;</span></p><p class=\"MsoNormal\"><span lang=\"NL-BE\">&nbsp;</span></p><p class=\"MsoNormal\" style=\"margin-bottom:12.0pt\"><span lang=\"NL-BE\">Best regards,</span><span lang=\"NL-BE\" style=\"font-size:11.0pt\"></span></p><p class=\"MsoNormal\" style=\"margin-bottom:12.0pt\"><b><span lang=\"NL-BE\" style=\"font-family:&quot;Agency FB&quot;,sans-serif; color:#FD6035\">Anas Benabbou</span></b><span style=\"font-family:&quot;Agency FB&quot;,sans-serif\"></span></p><p class=\"MsoNormal\" style=\"margin-bottom:12.0pt\"><span lang=\"NL-BE\" style=\"font-size:8.0pt; font-family:&quot;Verdana&quot;,sans-serif; color:black\">Tel&nbsp;: 0032 3 205 60 21 (Direct)</span><span lang=\"NL-BE\" style=\"font-size:8.0pt; font-family:&quot;Verdana&quot;,sans-serif; color:#2A2A2A\"><br></span><span lang=\"NL-BE\" style=\"font-size:8.0pt; font-family:&quot;Verdana&quot;,sans-serif; color:black\">Mail : </span><span lang=\"NL-BE\" style=\"font-size:8.0pt; font-family:&quot;Verdana&quot;,sans-serif\"><a href=\"mailto:Anas.benabbou@dkm-customs.com\"><span style=\"color:#0563C1\">Anas.benabbou@dkm-customs.com</span></a><span style=\"color:black\"> </span></span><span lang=\"NL-BE\"><br></span><span lang=\"NL-BE\" style=\"font-size:8.0pt; font-family:&quot;Verdana&quot;,sans-serif; color:black\">Mail :</span><span lang=\"NL-BE\" style=\"font-size:8.0pt; font-family:&quot;Verdana&quot;,sans-serif; color:#0563C1\"> </span><span lang=\"NL-BE\" style=\"font-size:8.0pt; font-family:&quot;Verdana&quot;,sans-serif\"><a href=\"mailto:import@dkm-customs.com\"><span style=\"color:#0563C1\">import@dkm-customs.com</span></a></span><span lang=\"NL-BE\"><br></span><span lang=\"NL-BE\" style=\"font-size:8.0pt; font-family:&quot;Verdana&quot;,sans-serif\">Visit our :</span><span lang=\"NL-BE\"> <a href=\"https://eur01.safelinks.protection.outlook.com/?url=https%3A%2F%2Fwww.linkedin.com%2Fcompany%2Fdkm-customs%2F&amp;data=05%7C02%7Cfoldermill%40dkm-customs.com%7C5a9580bba9174ce5b00108dcf40b8ed2%7Ca696cf459e704909a6742391335b26a9%7C0%7C0%7C638653578628866607%7CUnknown%7CTWFpbGZsb3d8eyJWIjoiMC4wLjAwMDAiLCJQIjoiV2luMzIiLCJBTiI6Ik1haWwiLCJXVCI6Mn0%3D%7C0%7C%7C%7C&amp;sdata=CyU%2FkCIkErFvwmP42B%2BEUGGUApCrGTNmpDeFXnd1gWU%3D&amp;reserved=0\" originalsrc=\"https://www.linkedin.com/company/dkm-customs/\" shash=\"tYaQtuve871FtJtiZxMnt43qkjhbZGTF9QZ+S2YWYrJNxjqtjLwFSi+wfvDg/YWTd05HFXrbZP/BQnfco2dwyAdhEVjAz7/xDQzFPrKbbF/kfbiDToQ7/Msn4EUY6Pzr7q2xL1ouiP93bffvGe53xxNgT9za7QC9wDVZyIHPBuM=\" title=\"Linkedin-page\"><span style=\"font-size:8.0pt; font-family:&quot;Verdana&quot;,sans-serif; color:#0563C1\">LinkedIn-page</span></a></span></p><p class=\"MsoNormal\" style=\"margin-bottom:12.0pt\"><a href=\"https://eur01.safelinks.protection.outlook.com/?url=https%3A%2F%2Fdkm-customs.com%2F&amp;data=05%7C02%7Cfoldermill%40dkm-customs.com%7C5a9580bba9174ce5b00108dcf40b8ed2%7Ca696cf459e704909a6742391335b26a9%7C0%7C0%7C638653578628894365%7CUnknown%7CTWFpbGZsb3d8eyJWIjoiMC4wLjAwMDAiLCJQIjoiV2luMzIiLCJBTiI6Ik1haWwiLCJXVCI6Mn0%3D%7C0%7C%7C%7C&amp;sdata=qy13esNW61cZWCip%2F4zGsMMaTH%2FqII1P9UO27evKuS0%3D&amp;reserved=0\" originalsrc=\"https://dkm-customs.com/\" shash=\"CjpXk0VZYoJVperwAJx65XgFqEQJy2Sys4OMtz11Kmq+NNWOncgMg8+i575eNH2tdh5dm4DQFioxFz8AWdP9M1lf8kKAQBWfEBo1ja3uufJ5ArYbF9U6shhceYMvIHkHDbzShopcGPumAVEX0M/ldsoDumR2JAF1go9Eex7wTWY=\"><span lang=\"NL-BE\" style=\"color:windowtext; text-decoration:none\"><img border=\"0\" width=\"597\" height=\"132\" id=\"Picture_x0020_6\" src=\"cid:image001.jpg@01DB25FC.CE010040\" alt=\"A close-up of a sign\n\nDescription automatically generated\" style=\"width:6.2187in; height:1.375in\"></span></a><u><span lang=\"NL-BE\" style=\"font-size:8.0pt\"></span></u></p><p class=\"MsoNormal\">&nbsp;</p></div></body></html>"

print(extract_office_value(extract_body_text(text)))