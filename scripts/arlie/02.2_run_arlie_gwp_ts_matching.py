import os
import argparse
from pathlib import Path
import geopandas as gpd
import pandas as pd
from globallakevariability.matching.arlieProcessor import make_arlie_files_to_dict, make_gwp_files_to_dict, find_min_max_length
import json
def main(config):

    input_root = Path(config['root_dir'])

    arlie_root = input_root / config['matching']['output_directory']
    gwp_root = input_root / config['path_to_gwp_timeseries_folder']
    lat_lon_root = input_root / config['path_to_coordinate_folder']

    max_disruption_threshold = config['matching']['maximum_disruption_threshold_perc']

    arlie_files = [arlie_root / file for file in os.listdir(arlie_root)]
    print(f"Total amount of arlie files: {len(arlie_files)}")
    print("Processing Arlie files ...")

    arlie_dict, lakes_to_check = make_arlie_files_to_dict(
        arlie_files, 
        max_area_difference=config['matching']['max_area_difference'],
        max_disruption_threshold=max_disruption_threshold
    )

    print(f"Found {len(arlie_dict)} valid ARLIE lakes")
    print(f"Lakes to check: {len(lakes_to_check)}")
 
    # Filter problematic lakes

    hylak_ids_to_filter = set(lakes_to_check['Hylak_id'])
    gwp_arlie_dict_filtered = {
        k: v for k, v in arlie_dict.items()
        if not any(hylak_id in hylak_ids_to_filter for hylak_id in v['Hylak_id'].values)
    }
    
    print(f"After removing problematic lakes: {len(gwp_arlie_dict_filtered)} lakes")
    

    # Process GWP files
    print("Processing GWP files...")
    
    gwp_arlie_dict = make_gwp_files_to_dict(gwp_root, gwp_arlie_dict_filtered, lat_lon_root=lat_lon_root)

    print(f"Amount of matching gwp arlie samples {len(gwp_arlie_dict)}")

    # Filter by minimum data points
    min_length, max_length, cleaned_dict, length_info_df = find_min_max_length(
        gwp_arlie_dict, 
        min_length_to_keep_df=config['matching']['min_length_to_keep_df']
    )
    
    print(f"Minimum DataFrame length: {min_length}")
    print(f"Maximum DataFrame length: {max_length}")
    print(f"Number of removed empty DataFrames: {len(gwp_arlie_dict) - len(cleaned_dict)}")
    print(f"Number of DataFrames for Analysis: {len(cleaned_dict)}")

    OUTPUT_Data = input_root / config['matching']['processed_data_directory']
    OUTPUT_Data.mkdir(parents=True, exist_ok=True)
    print(OUTPUT_Data)
    print(OUTPUT_Data / f"{config['matching']['filename_gwp_arlie_matching_summary']}.csv")
    for key, value in cleaned_dict.items():
       value.to_excel(OUTPUT_Data / f"{key}_cleaned.xlsx")
    # Save length info
    length_info_df.to_csv(OUTPUT_Data / "lake_lengths.csv", index=False)

    all_lakes = pd.concat(cleaned_dict.values())
    all_lakes.to_csv(OUTPUT_Data / f"{config['matching']['filename_gwp_arlie_matching_summary']}.csv")
    all_lakes.to_excel(OUTPUT_Data / f"{config['matching']['filename_gwp_arlie_matching_summary']}.xlsx", float_format="%.6f", index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Hydrolakes and GWP data based on configuration file.")
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
