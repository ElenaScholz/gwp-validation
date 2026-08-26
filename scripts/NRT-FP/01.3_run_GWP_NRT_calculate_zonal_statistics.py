import rasterio as rio
import rasterstats
import pandas as pd
import geopandas as gpd
import numpy as np 
import os
from pathlib import Path

from globallakevariability.preprocessing.zonal_statistics import  process_tile_year
import argparse
import re
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging
from tqdm import tqdm
import json

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zonal_stats_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)



def main(config):
    chunk_size = config['zonal_statistics']['chunk_size']
    num_workers = config['zonal_statistics']['num_workers']
    root = Path(config["root_dir"])
    gwp_path = root / config['preprocessing']['output_dir_gwp_nasaflood']
    mwp_basepath = root / config['preprocessing']['output_dir_nasaflood']
    max_extent_path = root / config['zonal_statistics']['max_extent_path'] 

    output_path = root / config["zonal_statistics"]["output"]
    # create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    all_results = []

    # process each tile-year combination
    for tile in config['zonal_statistics']["tiles"]:
        for year in config['zonal_statistics']["years"]:
            result_df = process_tile_year(tile, year, gwp_path, mwp_basepath,
                                          max_extent_path, chunk_size, num_workers,
                                          config['zonal_statistics']['max_files_per_tile_year'])

            if not result_df.empty:
                all_results.append(result_df)

                # optional: save intermediate results for this combination
                intermediate_file = output_path / f"intermediate_{tile}_{year}.csv"
                result_df.to_csv(intermediate_file, index=False)
                logger.info(f"Intermediate results saved to {intermediate_file}")

    # combine all results
    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        logger.info(f"Total result: {len(final_df)} rows")

        # group by Hylak_id and save separate files
        logger.info("Grouping results by lake...")
        lake_groups = final_df.groupby("Hylak_id")

        for hylak_id, lake_df in lake_groups:
            lake_name = lake_df["Lake_name"].iloc[0] if "Lake_name" in lake_df.columns else "Unknown"
            lake_name = lake_name if pd.notna(lake_name) else "Unnamed"

            # Sanitize lake_name for filename
            lake_name = re.sub(r'[\\/*?:"<>|]', "_", str(lake_name))
            file_name = output_path / f"Lake_{hylak_id}_{lake_name}.csv"

            lake_df.to_csv(file_name, index=False)
            logger.info(f"Lake {hylak_id} ({lake_name}) saved to {file_name}")

        # also save the combined results
        final_df.to_csv(output_path / "all_lakes_combined.csv", index=False)
        logger.info("All results saved")
    else:
        logger.warning("No results found!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate zonal statistics for GWP and Nasa Flood Product")
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


