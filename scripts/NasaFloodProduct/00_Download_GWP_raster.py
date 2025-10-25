# This Script automatically downloads GWP data from the dlr server

import os
import requests
from datetime import datetime, timedelta
# ========= USER INPUT ======================

start_date = datetime(2003,1,1) # yyyy, m, d 
end_date = datetime(2024, 12, 31)

outdir ="T:/DLR/Analysis3/Input/NasaFlood/01_GlobalGWP" 


# === SETUP ===
if not os.path.exists(outdir):
    os.makedirs(outdir)

# === LOOP THROUGH EACH DAY ===
current_date = start_date
while current_date <= end_date:
    ymd_str = current_date.strftime("%Y%m%d")
    year = current_date.year
    month = current_date.month
    day = current_date.day

    filename = f"GWP.OSWF.DAILY.{ymd_str}.v1.tif"
    url = f"https://download.geoservice.dlr.de/GWP/files/daily/{year}/{month:02d}/{day:02d}/{filename}"
    output_path = os.path.join(outdir, filename)

    if os.path.exists(output_path):
        print(f"Already exists: {filename}")
        current_date += timedelta(days=1)
        continue

    print(f"Downloading: {filename}")
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Saved: {output_path}")
        else:
            print(f"File not found (HTTP {response.status_code}): {filename}")
    except Exception as e:
        print(f"Download error for {filename}: {e}")

    current_date += timedelta(days=1)
