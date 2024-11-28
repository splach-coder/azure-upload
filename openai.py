import requests

url = "https://chatgpt-vision1.p.rapidapi.com/ocrvision"

payload = { "img_url": "https://cdn.handwrytten.com/www/2020/02/home-hero-photo2%402x.png" }
headers = {
	"x-rapidapi-key": "af1924dba8mshf7c475aa474866fp1c2f94jsn5413f22649fe",
	"x-rapidapi-host": "chatgpt-vision1.p.rapidapi.com",
	"Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())