import requests
from typing import Dict, Optional
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def fetch_tracking_data(tracking_number: str, operator: str = "MAEU") -> Optional[Dict]:
    """
    Fetch tracking data from Maersk API
    
    Args:
        tracking_number (str): The tracking number to look up
        operator (str): The operator code (default: MAEU)
    
    Returns:
        Optional[Dict]: The response data as a dictionary, or None if the request fails
    """
    # Setup session with retry strategy
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # API endpoint
    url = f"https://api.maersk.com/synergy/tracking/{tracking_number}?operator={operator}"

    # Headers
    headers = {
        'Host': 'api.maersk.com',
        'accept': 'application/json',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8',
        'akamai-bm-telemetry': 'a=49FA009199B17483A2DC090D1F37B1F3&&&e=NUY1NDc2NURGRDE4ODY2NjA4RUU2RTgxNzhDODE4NUZ+WUFBUUJ6WVRBbG12b3N5VEFRQUEzZm5ISnhxUGw2YkZzZHpXNTZjUFd2WGN0cDUwWm92K0dsSWhnaXI3QTVvSzJXSSs0V0xOMmJmei9HbW1aaUtQZzZjUHFBdXZZUnc3TGVBbHZzZHJjYU5YMFpJTUg0Z1ZJWE9sak1Xa1Q1c3lxZVRBR1p0bnltR2I5NU9NOEtOemxGNmQrU2lvamZYQ0VzSDlNdTlhN0RKcjhvU3ovSTl2aFBxRmR1UC9IQWtKSFc0bHdxRnhqL25LMFJ5WkxJM21ydHhBdy9ibERHWkpuWFp3aFloZFJqaWRTU3ZZekNwdGcvYlNSNlBSRmVlU1FMbWluTzlzOTZZWmovSVdRelFtbDEyRFNJc05pTGFmRG11MkVidThjd296T25JZkNNZzN6M0xoVDJPNVh6bDc2SGNDaDhYekJueEUrSndtZ2s2ZU9iNFZCY3NxWFp1NzdXUkFlbFJ0cDV6aFIvK1cwa3AwNTBEMys1NjlBNmw0MHdINFprQmU5Vnh5K0lIRm9aOFphTWFVMUVMWVdicDhQYkliVzZUMn4zMzU1NDQxfjQyNzc1NzA=&&&sensor_data=MzsxOzI7MDszMzU1NDQxOy9aT1pKQUxVVmdqaWZSM1FNTm80elMzZ2RXclEyUGZEY3ZRTFl5bUxuZFE9OzIxLDEsMCwxLDQsMDtiKzI+OTkiQl5WOiI5IilUXWJSRkgmajE7KVdQOGl2SiBrYV89e2E9b1h3fTRaMUg3OE5eWXh2JixfIksiTWE8IlkiKyw2MUZjJTReeHJsYit6ckFGKGpdT0MrMGsqVHdIY29BQClmVypDNnplZX16dE9kZyhiJDdjIjwiOXopImEiXjJFZCI8IlpdWCIuIlMpM1dhaV5aIjI8ISJLdzQiclIrWWdxdmAiYT9FIiZCUnF3eG51JWIiXlhUImQsXz9xRitVIiBzMSJZSEE6VHA0NE5vLj0rPFoiLzZeIipCLm5RIldyPz4iVCJBWWw6QSJsOWYiJjo2a24iKklsO2ZZZSJOU34+U1c3NENAc3NZTER0Pmc5O0xhQXtCbjYua1VjblNxMXNjdWtWXV4/PHI1cj4oRVcqQkYmP1EsWE0lIy4yJmk6UFdiSTVIb2dNLV5YRSFpV3ElcVNEWzZsZ01HQEA0cypqK0ZDMHUuWyRyR0FbbFUzdDYscjRTPXhwXyJFYEoiZUl3ImFQZ2dVdiJCMGllJmoqIm0ifEA0aHNkfG9+andVRyI4ImU3USI6dlk2fnp3V1k2JCJGZlgidWltYWpbQHhtZzVDcTxQOmpnRCIrL2UiNGNhXiRWQCIgMVZTIjU8InJKbSJ1OGYiaVdDKkFILXJBc3IkWzZ8cyAiLz9dWSI1Lk8zMCJeLTJnIjoiIDt0cyJuInNPOSJVImcsSmpzNiUxbkZPYEYhIkxiSyJCYjoiSyB7NXIiRFErImoiIkYiQFUwIl9vOyZ5Im9WIk0iIkciQ2opImwiIiZ5eU14eEc8InVpUyJWNSEkMCJQR2IiLiJRIiFyVCJlMkQibzdYdyste2UiQHhwIjxZWSZ+QjQib1ksYCJeQm0iTHtWKiJDIkI4UClSIm8xfiJPYXEidnhYSHxKUSJ0P3BJKSJIfj8icWhTIisiImsiMzBpInt5dHJtImJOIkciKkxDaWB7YHc8OkJpQzxKImYiKWYoIisiIiYicigwIisiInoie2FCIk5KTmc5ayIiPiJfQlgidTo1PXlaRlt+InxTPCI5cUhZJSNmPXtuKT4icDwoSCJpIiIkQUwiUlEiZCIzbyI1MVYiLDVsbCJAIihmKnU/JD5jfSBrXnR6USh6V19GRSJvIlZpNSIoMzdnICI8Jngid1Nhc11DYHtZKjBub2JrQkdtImR0ayIyRHZALmxVfXImImMyICJTInllVFYrcXhuWDt8IkYuQCI7ImpiPS9zIDF2fkhSXXYkcFciayJOWGMib1JXNygiPDwiNX5kWkNDU05jIm94RGJ3InAiImciWF5GIjZiZ10mTjFpZFVTP0F4Q340IiVaMCJCIiJYIlVXVyJ2YVsiXXxVIlM+JS1uIk0yIl5gTkFdIjw/UyJGImAiY2EzIl1sMCItIm1tc2J3WU1wWGVlSisjJjg9dSI/IkkvPiJ6IiJqIiNbIjZIQUo2JGUzIkkqbyI5Ulo2OWByKyIjZj8iO3hWWkVVQWlQIlFIIjRFY019LC4iUnxLdCJ5InlmImAlVSIvcz5AIik4OCJdO2kiQiIiKGBrIkouMCI8RCRRQCIodSYicSIyIkFVRiJ0Qk4iaSJhNlg0Y2UiU1t6XyJuO3siYGs3IjgiNjRLOyxTfXxnITchZklJQmdBRXN0cUVpP1g5a3JPXjQ3Z1BoTjhDYzR4d3l+JSI8ZkMiaXJgIj8vIEBAcnwiWjIiLVsiM1FmIk8zQCJAJmEiSGUqcyZWQCtsOlosQD81cyxsTVAhVG9zQ1trQkcmbDs4SnslInIiOzRdInYiIihufCIwRDkiNyIiNiJMNHEiKiIiZiJmPikiYDBGc1FBcCIiKSImZlkiTXQ3NWkiRz18eCJQIiJKIiFAZSI6aVRRRzlib3tnSyJ4QCN2Ii1wbTVAV3IiPCsoQFElST5mVjx5RSwxR0AuUWtRNTNxJHV+cGg+MU59IlIibT8gIg==',
        'api-version': 'v2',
        'consumer-key': 'UtMm6JCDcGTnMGErNGvS2B98kt1Wl25H',
        'origin': 'https://www.maersk.com/',
        'priority': 'u=1, i',
        'referer': 'https://www.maersk.com/',
        'sec-ch-ua': 'Microsoft Edge;v=131, Chromium;v=131, Not_A Brand;v=24',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': 'Windows',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.'
    }

    # Cookies
    cookies = {
        '_abck': '6923CDCCEFB4ED857306F1759EB705E4~-1~YAAQDzYTAu8duq6TAQAAO9oTLA1ljJGRlzVNi10abDZNWZqGK4k4HMBSGQVjdcvHAxEY8W9QddzE79TT32qNiKGkgmBdd7QTPnZzRvoF2mFPoswmxeJ6mXz8Jejvbivt7nsngT9xKHYlA4doM6xt/WlIxJLpI8MOFsW+ju5ChcBPRfE4TaV9rFtAqR5GWopjFNebPxgwnSsy8+GAdKLPN6oF84FWoT8wJa9VmNW/j/kskCPTYEbIpfgxT2GgMYFMfSOrYgu2XEhsU/itLQTB4P6yQLC7LYhZ4dJJUOXkNC88unea/aFxgM8tDxWHCx6lBLnMMkrHauQ8o2rsGIKD5ivP6gDMkpVURDbt0tcOLCS5MUlpZ/BZSgXfuoc9tff0OqovadjoVluc9a57MSaztZHeHT8DVo0NHDiK5LdYq+G48CUzu7yGDd/P0jMusvN4YqvF5rTbnch+rtkJnDFDibiTC6CfsZbjbUB8NlMFmn6ibwLx6zdpgoRC03fYm4C9KeQ9xL329wT7iUwbMpez3PblY5p0zbSJqSLenbNkGxWIiTm78JeK7ZgScbJoWjSop+jkblxiKtiiGtVbU40SUlkRGWPbAuxxozA0Ds6YAOoDHuI3wKUv8qYurSJKB+vNu2vRPsa/Sx7KnRX8YRuwOxL0PYZXGgJNgEM=~-1~-1~-1',
        'bm_sz': 'F8B235C7321C844C543E2F9E2F789BB3~YAAQDzYTAsJGt66TAQAArv0ILBpP2BYIgAJ8ylQXDOvphyvFvC8Mf39t6wOFq9bOQ0Lq8Wj7jheJFNyALC3+4xt6ZS9MMA7k+wVgmrpQBRiJe3FRPqEnSlmNw5aqEvOPH9lT3zRWaQU14umn7VjnSSkTJdpjuR3V9dW2qDJ1jz5F70XQ/Daqugne6H4sQM4KoDS4JUTe0g4os3wjSr0/ky5zyQxoC9Xem/GX8cUhgGpTdBsQ31i1HYhjfGbImovZq6fHyFxIUPgHUZ/w+VjKA8PI+kHyYJAgyYBt0PNp+l9kY8ebqI3FSn9n9ivt1N7Xxns+mdSuogf5++2laZLDqs0Y8XXWGvhXi6v0BbMFmA==~3616821~4337986'
    }

    try:
        response = session.get(
            url,
            headers=headers,
            cookies=cookies,
            timeout=30,
            verify=True
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error making request: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Status Code: {e.response.status_code}")
            print(f"Response Text: {e.response.text}")
        return None

# Example usage
if __name__ == "__main__":
    tracking_data = fetch_tracking_data("278109465")
    if tracking_data:
        print("Tracking Data:", tracking_data)