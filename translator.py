from datetime import datetime

# Get the current year and month in "YYYYMM" format
current_date = datetime.now().strftime("%Y%m")

# Insert the dynamic part into the URL
url = f"https://www.belastingdienst.nl/data/douane_wisselkoersen/wks.douane.wisselkoersen.dd{current_date}.xml"

print(url)
