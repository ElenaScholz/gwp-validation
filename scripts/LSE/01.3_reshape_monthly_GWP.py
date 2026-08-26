import argparse
import json
def main (config):
    import pandas as pd
    from pathlib import Path
    import os
    import geopandas as gpd
    ROOT = Path(config['root_dir'])
    OUTPUT_FOLDER = ROOT / config['preprocessing']["monthly_gwp_folder"]
    INPUT_FOLDER = ROOT / config['path_to_gwp_timeseries_folder']
    hylak_ids = ROOT / config['preprocessing']['glakes_hylak_strict']
    all_gwp_files = os.listdir(INPUT_FOLDER)
    hydrolakes_gdf = gpd.read_file(hylak_ids)
    print(hydrolakes_gdf.columns)
    coordinates_df = hydrolakes_gdf[['latitude', 'longitude', 'Hylak_id', "Filename"]].drop_duplicates(subset='Hylak_id').reset_index(drop=True)
    coordinates_df['Hylak_id'] = coordinates_df['Hylak_id'].astype("int")
    print(coordinates_df.columns)
    # add the 'Hylak_' prefix and build the lookup dictionary
    coordinates_df['Lake_Hylak_id'] = 'Hylak_' + coordinates_df['Hylak_id'].astype(str)
    lat_lon_dict = coordinates_df.set_index('Lake_Hylak_id')[['latitude', 'longitude']].to_dict(orient='index')

    print(coordinates_df.head())

    gwp_lse_monthly = {}



    # Create a mapping from the file key to Hylak_id using coordinates_df
    id_map = dict(zip(coordinates_df['Filename'], coordinates_df['Hylak_id']))

    gwp_lse_monthly = {}
    monthly_gwp_dict_hylak_ids = {}

    for file in all_gwp_files:
        df = pd.read_csv(INPUT_FOLDER / file, sep=";", parse_dates=["Date"], index_col="Date")
        df_monthly = df.resample('MS').median()
        gwp_lse_monthly[file] = df_monthly

        # Directly get Hylak_id from id_map using the filename
        hylak_id = id_map.get(file)
        df_monthly['Hylak_id'] = hylak_id
        new_key = f'Hylak_{hylak_id}'
        monthly_gwp_dict_hylak_ids[new_key] = df_monthly

    # Save monthly timeseries with Hylak IDs
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    for file, df in monthly_gwp_dict_hylak_ids.items():
        filename = file + ".csv"
        df.to_csv(OUTPUT_FOLDER / filename, sep=";")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="reshape daily GWP LSE data to monthly")
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
