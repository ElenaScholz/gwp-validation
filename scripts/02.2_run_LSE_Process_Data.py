import pandas as pd
from pathlib import Path
import os
import argparse
import json
def main(config):
    ROOT = Path(config['root_dir'])

    INPUT_FOLDER = ROOT / config['matching']['output_dir']
    OUTPUT_FOLDER_Statistics = ROOT / config['matching']['statistics_output']
    OUTPUT_FOLDER_TimeseriesPlots = ROOT / config['matching']['output_ts_plots']
    OUTPUT_FOLDER_Statistics.mkdir(parents=True, exist_ok=True)
    OUTPUT_FOLDER_TimeseriesPlots.mkdir(parents=True, exist_ok=True)

    # Read in the glakes based dataset
    li_files = {}
    for file in os.listdir(INPUT_FOLDER):
        filename = file[:-4]  # Remove the .csv extension
        df = pd.read_csv(INPUT_FOLDER / file, sep=',')
        if df['li_lake_surface_area'].isna().all():
            print(f"Skipping {filename} as it contains only NaN values in 'li_lake_surface_area'.")
            continue
        else:
            df['gwp_Area_max_km2'] = df['gwp_Area_max'] * 1e-6  # Convert from m² to km²
            df['li_lake_surface_area_km2'] = df['li_lake_surface_area'] * 1e-6  # Convert from m² to km²
        # Ensure 'Date' is a datetime object
        df['Date'] = pd.to_datetime(df['Date'])

        # Remove all rows with dates from 2024
        df = df[df['Date'].dt.year != 2024]
        li_files[filename] = df

    # save these files for timeseries plots
    for glake, df in li_files.items():
        output_path = OUTPUT_FOLDER_TimeseriesPlots / f"{glake}_ts.csv"
        df.to_csv(output_path, index=False)
        print(f"Saved {output_path}")

    non_frozen_dict = {}
    # Remove all frozen tags for statistical analysis
    for glake, df in li_files.items():
        df_cleaned = df[df['frozen'] != True].copy()  # Remove rows where frozen is True
        non_frozen_dict[glake] = df_cleaned

    non_frozen_strict = {}
    # Remove all lakes where any month is frozen
    for glake, df in li_files.items():
        if df['frozen'].any():
            print(f"Excluding {glake} entirely due to presence of frozen months.")
            continue
        non_frozen_strict[glake] = df

    # combine all dfs in this dictionary into a dataframe
    combined_df = pd.concat(non_frozen_dict.values(), ignore_index=True)
    combined_df.to_csv(OUTPUT_FOLDER_Statistics / "LSE_all_lakes_no_frozen.csv", index=False)
    combined_df_with_frozen = pd.concat(li_files.values(), ignore_index=True)
    combined_df_with_frozen.to_csv(OUTPUT_FOLDER_Statistics / "LSE_all_lakes_with_frozen.csv", index=False)
    combined_df_strict = pd.concat(non_frozen_strict.values(), ignore_index=True)
    combined_df_strict.to_csv(OUTPUT_FOLDER_Statistics / "LSE_all_lakes_strict_no_frozen.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="match GWP with Li Dataset - File 2")
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

