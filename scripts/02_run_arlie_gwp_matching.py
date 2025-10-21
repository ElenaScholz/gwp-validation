from zipfile import ZipFile
import os
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely import wkt
from globallakevariability.matching.arlieProcessor import ArlieProcessor, create_gwp_based_dict, find_multiple_assignments, drop_multiple_assigned_hylaks
import argparse
from globallakevariability.utils.helper import save_dict
import json

def main(config):

    input_root = Path(config["root_dir"])
    arlie_root = input_root / config["path_to_arlie_folder"]

    # hylak_ds = gpd.read_file(config["path_to_hydrolake_dataset"])   
    #     # Umbenennen der 'id' Spalte zu 'gwp_id'
    
    path_hydolakes_with_gwp = config['preprocessing']['gwp_hydrolakes_max_extent']
    df_gwp_hylakIds = gpd.read_file(path_hydolakes_with_gwp)
    #print(df_gwp_hylakIds.columns)
    df_gwp_hylakIds = df_gwp_hylakIds.rename(columns={'id': 'gwp_id'})
    df_gwp_hylakIds = df_gwp_hylakIds[['Hylak_id', 'gwp_id', 'gwp_Area_max']].copy()
    
    arlieProcessor = ArlieProcessor(root_to_arlie_folder= arlie_root,
                                  path_to_hylak_dataset= config["path_to_hydrolake_dataset"],
                                  gwp_dataset_with_hylak_ids= df_gwp_hylakIds)

    arlie_geoms = arlieProcessor.prepareArlieGeometries()
    arlieProcessor.filter_by_overlap_threshold(threshold_percentage=10)
    arlieProcessor.matchArlieAndGWP()
    stats_dict = arlieProcessor.mergeArlieStatsWithGeoms()

    print(arlie_geoms.keys())
    print(f"lenght of arlie statistics dict: {len(stats_dict.items())}")

    gwp_arlie_dicts = create_gwp_based_dict(stats_dict)
    arlie_to_hylak, multiple_assignments = find_multiple_assignments(gwp_arlie_dicts)
    filtered_dict = drop_multiple_assigned_hylaks(multiple_assignments, gwp_arlie_dicts)
    out_dir = input_root / config["matching"]["output_directory"]
    save_dict(filtered_dict, output_path=out_dir)


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