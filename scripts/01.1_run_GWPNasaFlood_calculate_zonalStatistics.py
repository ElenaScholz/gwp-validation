import rasterio as rio
import rasterstats
import pandas as pd
import geopandas as gpd
import numpy as np 
import os
from pathlib import Path
from globallakevariability.preprocessing.filehandling import get_filepaths_from_folder 
from globallakevariability.preprocessing.zonal_statistics import concat_gwp_and_mwp, calculate_zonal_statistics, find_matching_files, process_in_batches, process_file_pair, process_tile_year
import argparse
import re
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging
from tqdm import tqdm
import json

# Konfiguriere Logging
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
    # Erstelle Output-Verzeichnis, falls es nicht existiert
    output_path.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    
    # Verarbeite jede Tile-Jahr-Kombination
    for tile in config['zonal_statistics']["tiles"]:
        for year in config['zonal_statistics']["years"]:
            result_df = process_tile_year(tile, year, gwp_path, mwp_basepath, 
                                          max_extent_path, chunk_size, num_workers,
                                          config['zonal_statistics']['max_files_per_tile_year'])
            
            if not result_df.empty:
                all_results.append(result_df)
                
                # Optional: Speichere Zwischenergebnisse für diese Kombination
                intermediate_file = output_path / f"intermediate_{tile}_{year}.csv"
                result_df.to_csv(intermediate_file, index=False)
                logger.info(f"Zwischenergebnisse gespeichert in {intermediate_file}")
    
    # Kombiniere alle Ergebnisse
    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        logger.info(f"Gesamtergebnis: {len(final_df)} Zeilen")
        
        # Gruppiere nach Hylak_id und speichere separate Dateien
        logger.info("Gruppiere Ergebnisse nach Seen...")
        lake_groups = final_df.groupby("Hylak_id")
        
        for hylak_id, lake_df in lake_groups:
            lake_name = lake_df["Lake_name"].iloc[0] if "Lake_name" in lake_df.columns else "Unknown"
            lake_name = lake_name if pd.notna(lake_name) else "Unnamed"
            
            # Sanitize lake_name for filename
            lake_name = re.sub(r'[\\/*?:"<>|]', "_", str(lake_name))
            file_name = output_path / f"Lake_{hylak_id}_{lake_name}.csv"
            
            lake_df.to_csv(file_name, index=False)
            logger.info(f"See {hylak_id} ({lake_name}) gespeichert in {file_name}")
        
        # Speichere auch die Gesamtergebnisse
        final_df.to_csv(output_path / "all_lakes_combined.csv", index=False)
        logger.info("Alle Ergebnisse gespeichert")
    else:
        logger.warning("Keine Ergebnisse gefunden!")

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


