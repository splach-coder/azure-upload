import requests

# Set up Postman proxy settings
postman_proxy = "https://api.maersk.com/synergy/tracking/278109465?operator=MAEU."  # Replace 5555 with the port set in Postman

proxies = {
    "http": postman_proxy,
    "https": postman_proxy,  # Postman can handle both HTTP and HTTPS
}

# Your target URL
url = "https://example.com/api/endpoint"

cookies = {
    '_abck': '6923CDCCEFB4ED857306F1759EB705E4~-1~YAAQDzYTAliE5q6TAQAAof/zLA0niMU8UkAu0naVBCFdC2hoNuy93o05DWWoOJ2zj63Zb3QTtfJW0rb5WZ40cwIJFz7j/EWAIbdO5uQXbXW/RimRcYlvbJ+ggTxaFI7HALHqfbEb7RcfUkkBZR+fvEN7a3BKidz8ECSE1orxZZviHoD3MSLApo7COhHHt1bL86Dbtt3x0JvK5V9FqcmGQBUAVJBxMcTG9Znj2Tt6rXq6b+6nEG9ysuCNdHZWRrdt7ZUVY5OUJXR2qA06dXC8Iss+UjzhoCNwY0LIy0X1BzeeiCqWd/itVUrCd9/2bL0JoizPCONp7OcvG7LIoJhN3ffzynU91GrkkoZ7uE4uIJSf3Ppu03gaO3ZUHfBp2oBWaBUNtAPXWCra5FqUrq/WB0GugIzVL0/RpiesaNFyNP0sMkQR4RQt/DBRtQv/5jDQep+1h0Z+B+IZ47Cu1MtdsoQRnJsxoZ/Xq0cKb1EGdmWiuP7Fgr5nzKSbJszj0LAUTJcLTNa/UohxrzqWvRod8pfeeHxPMZ2HU7kSXsjdwL6HAHE1bbKNteigHZENJdMYgregMUc80vyP8k5BmvKc8XvqCDHYm+UBWMf47wDmxdysVyB1AXs49YTXiD1OKTMHTQLuIkhhzUxcKQVI5UmS4meTSUTHBnZLh6k=~-1~-1~-1',
}

headers = {
    'accept': 'application/json',
    # 'accept-encoding': 'gzip, deflate, br, zstd',
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
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.',
    'Cookie': '_abck=6923CDCCEFB4ED857306F1759EB705E4~-1~YAAQDzYTAliE5q6TAQAAof/zLA0niMU8UkAu0naVBCFdC2hoNuy93o05DWWoOJ2zj63Zb3QTtfJW0rb5WZ40cwIJFz7j/EWAIbdO5uQXbXW/RimRcYlvbJ+ggTxaFI7HALHqfbEb7RcfUkkBZR+fvEN7a3BKidz8ECSE1orxZZviHoD3MSLApo7COhHHt1bL86Dbtt3x0JvK5V9FqcmGQBUAVJBxMcTG9Znj2Tt6rXq6b+6nEG9ysuCNdHZWRrdt7ZUVY5OUJXR2qA06dXC8Iss+UjzhoCNwY0LIy0X1BzeeiCqWd/itVUrCd9/2bL0JoizPCONp7OcvG7LIoJhN3ffzynU91GrkkoZ7uE4uIJSf3Ppu03gaO3ZUHfBp2oBWaBUNtAPXWCra5FqUrq/WB0GugIzVL0/RpiesaNFyNP0sMkQR4RQt/DBRtQv/5jDQep+1h0Z+B+IZ47Cu1MtdsoQRnJsxoZ/Xq0cKb1EGdmWiuP7Fgr5nzKSbJszj0LAUTJcLTNa/UohxrzqWvRod8pfeeHxPMZ2HU7kSXsjdwL6HAHE1bbKNteigHZENJdMYgregMUc80vyP8k5BmvKc8XvqCDHYm+UBWMf47wDmxdysVyB1AXs49YTXiD1OKTMHTQLuIkhhzUxcKQVI5UmS4meTSUTHBnZLh6k=~-1~-1~-1',
    'Content-Type': 'application/x-www-form-urlencoded',
}

# Send the request through Postman proxy
response = requests.get(url, headers=headers, cookies=cookies, proxies=proxies, verify=False)

print(response.text)