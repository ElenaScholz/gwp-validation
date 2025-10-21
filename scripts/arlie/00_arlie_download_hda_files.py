"""
Download ARLIE dataset items using the HDA API and spatial query polygons.

This script:
1. Loads a GeoPackage file with polygon geometries.
2. Splits the geometries into chunks for multiple API requests.
3. Sends the requests to the HDA API using a MultiPolygon WKT.
4. Downloads matching data items to a specified output directory.
"""

import geopandas as gpd
from shapely.geometry import MultiPolygon
from hda import Client, Configuration
from pathlib import Path
import getpass

# === Step 0: Define Variables:
# Path to the Area of Interest (needs to be a gpkg file)

input_file = Path(r"...\not_downloaded_bBoxes2.gpkg") # Type in your path!

# Output directory for downloaded data
OUTPUT_PATH = Path(".../ARLIE") 

# Define Start- & Enddate
start_date = "2016-09-01T00:00:00.000Z"
end_date = "2025-04-01T23:59:59.999Z"

# Download geometry information besides the timeseries data
geometry_request = "True"

# === Step 1: Configuration and Authentication ===

# Path to HDA credentials file
hdarc = Path.home() / '.hdarc'

# If credentials are missing, ask user and create file
if not hdarc.is_file():
    USERNAME = input('Enter your WEkEO username: ')
    PASSWORD = getpass.getpass('Enter your password: ')

    with open(hdarc, 'w') as f:
        f.write(f'user: {USERNAME}\n')
        f.write(f'password: {PASSWORD}\n')
else:
    print('✅ Configuration file already exists.')

# Create HDA client instance
hda_client = Client()

# === Step 2: Load Geometries from File ===

# Path to GeoPackage with geometries to query
gdf = gpd.read_file(input_file)

# Extract individual geometries
geoms = list(gdf['geometry'])

# === Step 3: Chunking the Geometries ===

num_groups = 100         # Total number of groups to split into
start_group = 42         # Index to start from (e.g., resume from group 43)

# Distribute geometries across groups in round-robin fashion
chunks = [geoms[i::num_groups] for i in range(num_groups)]



# === Step 4: Loop Over Geometry Groups and Send API Requests ===

for idx in range(start_group, num_groups):
    chunk = chunks[idx]
    multipolygon = MultiPolygon(chunk)
    wkt_multipolygon = multipolygon.wkt

    print(f"\n📦 Group {idx + 1}/{num_groups}:")
    print(f"➡️ Sending WKT MultiPolygon with {len(chunk)} polygons")

    # Define HDA API query
    query = {
        "dataset_id": "EO:CRYO:DAT:HRSI_ARLIE",
        "startdate": start_date,
        "enddate": end_date,
        "requestGeometries": geometry_request,
        "geometryWkt": wkt_multipolygon,
        "itemsPerPage": 200,
        "startIndex": 0
    }

    print(f"🔍 Sending request for group {idx + 1}...")
    matches = hda_client.search(query)

    # Download if results found
    if matches:
        print(f"📥 Downloading {len(matches)} items for group {idx + 1}...")
        matches[-1].download(OUTPUT_PATH)
    else:
        print(f"⚠️ No results for group {idx + 1}.")
