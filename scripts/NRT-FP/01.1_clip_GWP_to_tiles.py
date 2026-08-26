# This script is supposed to clip GWP world maps to the Nasa Flood Product tiles.
# NOT READY
import os
import json
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import pandas as pd
from pathlib import Path
import argparse


def main(config):

    used_tiles_file = config["preprocessing"]["used_tiles_file"]
    gwp_worldmap_dir = config["preprocessing"]["GWP_WorldMap_Dir"]

    output_directory = config["preprocessing"]["output_dir_gwp_nasaflood"]
    os.makedirs(output_directory, exist_ok=True)

    tiles = gpd.read_file(used_tiles_file)
    used_tiles = tiles["MCDWDTile"].unique().tolist()

    gwp_files = [f for f in os.listdir(gwp_worldmap_dir) if f.endswith('.tif')]

    for tile in used_tiles:
        print(f"Processing tile: {tile}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clip GWP world maps to NASA Flood Product tiles based on configuration file.")
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help="Path to the JSON configuration file"
    )
    
    args = parser.parse_args()
    
    with open(args.config, 'r') as f:
        config = json.load(f)
    
    main(config)