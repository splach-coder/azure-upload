import os
import requests
from zipfile import ZipFile

# List of image URLs
urls = [
    "https://www.kasbahangour.com/wp-content/uploads/2019/10/GUARDIAN-ARTICLE-page-001.jpg",
    "https://www.kasbahangour.com/wp-content/uploads/2019/10/SAINSBURY-MAGAZINE-LOGO.jpg",
    "https://www.kasbahangour.com/wp-content/uploads/2019/10/E-AND-I-LOGO.jpg",
    "https://www.kasbahangour.com/wp-content/uploads/2019/10/LONDON-EVENING-STANDARD-LOGO.jpg",
    "https://www.kasbahangour.com/wp-content/uploads/2019/10/Retire-move-magazine-LOGO.jpg",
    "http://www.kasbahangour.com/wp-content/uploads/2019/10/BOE-JPG.jpg",
    "http://www.kasbahangour.com/wp-content/uploads/2019/10/OMOTG-LOGO.jpg",
    "https://www.kasbahangour.com/wp-content/uploads/2019/10/DAILY-TELEGRAPH-LOGO.jp"
]

# Create a folder to store the downloads
folder = "downloaded_images"
os.makedirs(folder, exist_ok=True)

# Download each image
for url in urls:
    filename = os.path.basename(url)

    # Fix incomplete extensions
    if filename.endswith(".jp"):
        filename += "g"

    filepath = os.path.join(folder, filename)

    print(f"Downloading {url} -> {filename}...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"Failed to download {url}: {e}")

# Create ZIP archive
zip_filename = "images_archive.zip"
with ZipFile(zip_filename, "w") as zipf:
    for file in os.listdir(folder):
        zipf.write(os.path.join(folder, file), file)

print(f"\nAll done! Images are saved in '{folder}' and zipped into '{zip_filename}'.")
