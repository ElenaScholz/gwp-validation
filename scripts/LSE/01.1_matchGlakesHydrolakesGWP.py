from pathlib import Path
import geopandas as gpd
import pandas as pd
import os
import json
import argparse
from globallakevariability.preprocessing.GlakesProcessor import GLAKESProcessor
from globallakevariability.preprocessing.postprocessingGlakes import merge_hylak_glakes_strict

def main(config):
    ROOT = Path(config['root_dir'])
    print("ROOT directory is set to:", ROOT)
    gwp_lakes = gpd.read_file(ROOT / config['preprocessing']['max_extent_dataset'])
    print("Loading GWP lakes from:", gwp_lakes)
    hydrolakes = ROOT / config['preprocessing']['hydrolakes_shp']
    print("Loading HydroLAKES shapefile from:", hydrolakes)
    glakes_dir = ROOT / config['preprocessing']['glakes_directory']

    glakes_prepared_dir = ROOT / config['preprocessing']['glakes_output'] / "glakes_hylak_30_subset.gpkg"
    if os.path.exists(glakes_prepared_dir):
        glakes_hylak_30 = gpd.read_file(glakes_prepared_dir)

    else:
        GlakesProcessor = GLAKESProcessor(glakes_dir, hydrolakes, gwp_lakes)
        glakes_shp = GlakesProcessor.prepare_GLAKES_geometries()
        hydrolakes_shp = GlakesProcessor.prepare_Hydrolakes_geometries()

        glakes_hylak_30 = GlakesProcessor.match_glakes_and_hylak(glakes_shp, hydrolakes_shp, threshold_percentage=30)
        glakes_hylak_30 = glakes_hylak_30[["GLAKES_id", "Hylak_id", "intersection_pct", "glakes_area", "geometry"]].copy()

        glakes_hylak_30.rename(columns={"intersection_pct": "Hylak_Glakes_intersection_pct", "geometry": "glakes_geometry"}, inplace=True)
        glakes_hylak_30.to_file(glakes_prepared_dir, driver="GPKG")

    
    gwp_lakes_subset = gwp_lakes[['id', 'latitude', 'longitude', 'Hylak_id', 'Filename', 'geometry', "gwp_Area_max"]]

    merged_lakes , hylak_ids_for_merge_with_liData = merge_hylak_glakes_strict(
        gwp_lakes_subset,
        glakes_hylak_30,
        hylak_key='Hylak_id',
        glakes_key='GLAKES_id',
        how='inner',
        verbose=True
    )

    print(merged_lakes.columns)
    # # drop glakes geometry column
    # merged_lakes = merged_lakes.drop(columns=['glakes_geometry'])
    # 'glakes_geometry'

    merged_path = ROOT / config['preprocessing']['glakes_output'] / "gwp_glakes_hylak_30_merged_strict.gpkg"
    merged_lakes.to_file(merged_path, driver="GPKG")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="match GWP lakes with GLAKES and HydroLAKES datasets")
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
