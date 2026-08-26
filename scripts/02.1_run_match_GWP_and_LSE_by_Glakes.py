from pathlib import Path
import geopandas as gpd
import pandas as pd
import os
import argparse
import json
def main(config):
    ROOT = Path(config['root_dir'])
    GWP_GLAKES_INFORMATION = ROOT / config['preprocessing']['glakes_hylak_strict']
    Li_Data_Folder = ROOT / config['preprocessing']['li_monthly_lakes_dir']
    GWP_DATA_FOLDER = ROOT / config['preprocessing']['monthly_gwp_folder']

    OUTPUT_FOLDER = ROOT / config['matching']['output_dir']
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 1 Read in all files

    # 1.1 this was generated in Li_00.1_HydrolakesGWPMatchGlakes.py
    matching_hydrolakes = gpd.read_file(GWP_GLAKES_INFORMATION)

    # 1.2 Read in all GWP and Li files into dictionaries
    gwp_dictionary = {}
    for file in os.listdir(GWP_DATA_FOLDER):
        if file.endswith(".csv"):
            filename = file[:-4]  # Remove .csv extension
            df = pd.read_csv(GWP_DATA_FOLDER / file, sep = ";")
            gwp_dictionary[filename] = df


    li_dictionary = {}
    for file in os.listdir(Li_Data_Folder):
        if file.endswith(".csv"):
            filename = file[:-4]  # Remove .csv extension
            df = pd.read_csv(Li_Data_Folder / file , sep=",")
            li_dictionary[filename] = df

    # 2. Make li and gwp a glakes based dictionary

    # 2.1 Li: 
    # 1️ Combine all DataFrames into one big DataFrame
    combined_li = pd.concat(li_dictionary.values(), ignore_index=True)

    # add glakes_id by merging with matching_hydrolakes
    combined_li = combined_li.merge(matching_hydrolakes[['Hylak_id', 'GLAKES_id']], on='Hylak_id', how='left')

    # 2️ Group by GLAKES_id and month
    agg_df_li = (
        combined_li.groupby(['GLAKES_id', 'month'], as_index=False)
        .agg({
            'lake_surface_area': 'sum',
            'frozen': 'any',  # True if any are True
            'Hylak_id': lambda x: list(set(x))  # unique list of contributing Hylak lakes
        })
    )

    # 3️ Optional: sort for readability
    agg_df_li = agg_df_li.sort_values(['GLAKES_id', 'month']).reset_index(drop=True)
    agg_df_li = agg_df_li.rename(columns={'lake_surface_area': 'li_lake_surface_area', "month": "Date"})

    # 2.2 GWP:
    # 1️ Combine all DataFrames into one big DataFrame

    combined_gwp = pd.concat(gwp_dictionary.values(), ignore_index=True)
    # add glakes_id by merging with matching_hydrolakes

    combined_gwp = combined_gwp.merge(matching_hydrolakes, on='Hylak_id', how='outer')

    print(combined_gwp.columns)
    # 2️ Group by GLAKES_id and month
    agg_df_gwp = (
        combined_gwp.groupby(['GLAKES_id', 'Date'], as_index=False)
        .agg({
            'Area': 'sum',
            'Hylak_id': lambda x: list(set(x)),  # unique list of contributing Hylak lakes
            'id': 'first',
            'Filename': 'first',
            'latitude': 'first',
            'longitude': 'first',
            'glakes_area': 'first',
            'gwp_Area_max': 'sum'
        })
    )

    print(agg_df_gwp.columns)

    # 3️ Optional: sort for readability
    agg_df_gwp = agg_df_gwp.sort_values(['GLAKES_id', 'Date']).reset_index(drop=True)
    agg_df_gwp.rename(columns={"Area": "GWP_lake_surface_area"}, inplace=True)

    # 3. Merge Li and GWP
    merged = pd.merge(
        agg_df_gwp,
        agg_df_li[['GLAKES_id', 'Date', 'li_lake_surface_area', 'frozen']],  # only the needed column
        on=['GLAKES_id', 'Date'],
        how='left'  # keep all from agg_df_gwp
    )

    # make merged a glakes based dict and store each file as a csv
    merged_dict = {glakes_id: df for glakes_id, df in merged.groupby('GLAKES_id')}
    Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)
    for glakes_id, df in merged_dict.items():
        output_path = Path(OUTPUT_FOLDER) / f"glakes_{int(glakes_id)}.csv"
        df.to_csv(output_path, index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="match GWP with Li Dataset")
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

