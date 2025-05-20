from bs4 import BeautifulSoup

def extract_email_body(html_content):
    """
    Extracts the visible body text from an Outlook HTML email.
    
    Args:
        html_content (str): The raw HTML content of the email.
    
    Returns:
        str: Cleaned plain-text body of the email.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Optionally: remove script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()

    # Find the <body> tag content if it exists
    body = soup.find("body")
    text = body.get_text(separator="\n") if body else soup.get_text(separator="\n")

    # Clean extra spaces and lines
    clean_text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())

    return clean_text

     
         