import os
import argparse
import json
from pathlib import Path

from globallakevariability.preprocessing.HydrolakesDataloader import HydroLakesGWP_DataLoading
from globallakevariability.preprocessing.filehandling import get_output_filename, get_csv_filename, get_gpkg_filename
from globallakevariability.preprocessing.add_max_extent import derive_max_extent_info, add_max_extent_to_gwp

def main(config):
    aoi = config["aoi"]
    root_dir = config["root_dir"]
    path_to_time_series_folder = config["path_to_gwp_timeseries_folder"]
    output_dir = root_dir + "/" + config["preprocessing"]["output_dir"]

    clip_to_arlie = (aoi == 'arlie')
    print(f"Processing Hydrolakes for AOI: {aoi}")

    output_path = get_output_filename(output_dir, aoi)
    print(output_path)
    gwp_timeseries_folder = os.path.join(root_dir, path_to_time_series_folder)
    
    hylak_processor = HydroLakesGWP_DataLoading(
        root_dir,
        clip_to_arlie
    )

    gwp_with_hylak_id = hylak_processor.load_and_join_hydrolakes_gwp()

    print(f"There are {len(gwp_with_hylak_id)} GWP samples with a matching Hydrolake for the further analysis")
    print(gwp_with_hylak_id)

    # Add max extent info

    max_extent_df = derive_max_extent_info(gwp_timeseries_folder)

    gwp_with_hylak_id_max_extent = add_max_extent_to_gwp(gwp_with_hylak_id, max_extent_df)
    # check if output directory exists, if not create it
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    print(f"Saving outputs to {output_dir}")

    gwp_with_hylak_id.to_file(output_path, driver="GPKG")
    gwp_with_hylak_id.to_csv(get_csv_filename(output_path, "noMaxExtent"), index=False)

    gwp_with_hylak_id_max_extent.to_file(get_gpkg_filename(output_path, "withMaxExtent"), driver="GPKG")
    gwp_with_hylak_id_max_extent.to_csv(get_csv_filename(output_path, "withMaxExtent"), index=False)

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



