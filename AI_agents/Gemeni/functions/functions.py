import ast
import requests


def convert_to_list(string_list):
    """Converts a string representation of a list into an actual Python list."""
    try:
        return ast.literal_eval(string_list)
    except (ValueError, SyntaxError):
        print("Error: Invalid list format in the string.")
        return None  # Or return an empty list, depending on your needs

def query_gemini(api_key, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

