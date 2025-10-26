import pandas as pd
from pathlib import Path
import numpy as np
import geopandas as gpd
from globallakevariability.stats.statistics import calculate_stats_per_lake 
import os
import argparse
import json

def main(config):

    arlie_number_of_sample = config["stats"]["arlie_number_of_sample"]
    nasaflood_number_of_sample = config["stats"]["nasaflood_number_of_sample"]
    li_number_of_sample = config["stats"]["li_number_of_sample"]
    
    ROOT = Path(config['root'])
    li_path = ROOT / config["input"]["li_data"]
    arlie_path = ROOT / config["input"]["arlie_data"]
    nasa_path = ROOT / config["input"]["nasaflood_data"]

    hydrolakes = ROOT / config["input"]["hydrolakes"]

    OUTPUT_DIR = ROOT / config['output']["dir"]
    os.makedirs(OUTPUT_DIR, exist_ok=True)


    glakes = pd.read_csv( li_path , sep=',') 
    arlie = pd.read_csv (arlie_path , sep=',')
    nasaflood = pd.read_csv(nasa_path, sep=',')


    arlie_subset = arlie[["date", "Hylak_id", "water_perc", "Latitude", "Longitude", "GWP_water_perc", "GWP_Area"]]
    arlie_subset =arlie_subset.rename(columns ={
        "date": "Date",
        "water_perc": "validation-water-perc",
        'GWP_water_perc': 'gwp-water-perc',
        'GWP_Area': 'gwp-area-km2'
    })

    arlie_subset['gwp-max-area-km2'] = arlie_subset['gwp-area-km2'].groupby(arlie_subset['Hylak_id']).transform("max")
    arlie_subset['gwp-water-perc-of-max'] = arlie_subset['gwp-area-km2']*100/arlie_subset['gwp-max-area-km2']

    arlie_subset

    nasaflood_subset = nasaflood[['date', 'mwp-total-water-perc', 'gwp-water-perc', 'Hylak_id', 'latitude', 'longitude', ]]

    nasaflood_subset =nasaflood_subset.rename(columns ={
        "date": "Date",
        "mwp-total-water-perc": "validation-water-perc",
        "gwp-water-perc": "gwp-water-perc",
        "Hylak_id": "Hylak_id",
        "latitude": "Latitude",
        "longitude": "Longitude"
    })


    glakes_subset = glakes[["Date", "GLAKES_id", "Hylak_id", "GWP_lake_surface_area", "gwp_Area_max_km2", "li_lake_surface_area_km2", "latitude", "longitude", "glakes_area"]].copy()

    # NOTE: some max_extents are missing in gwp_Area_max_km2, resulting in inf values in percentage calculation
    # therefore drop rows with  gwp_Area_max_km2 == 0.0
    glakes_subset.columns
    glakes_subset['gwp-max-area-km2'] = glakes_subset['GWP_lake_surface_area'].groupby(glakes_subset['GLAKES_id']).transform("max")
    glakes_subset['gwp-water-perc'] = glakes_subset['GWP_lake_surface_area'] / glakes_subset['gwp-max-area-km2'] * 100
    glakes_subset
    # glakes_subset = glakes_subset[glakes_subset['gwp_Area_max_km2'] > 0.0].copy()
    # glakes_subset['gwp-water-perc'] = glakes_subset['GWP_lake_surface_area'] / glakes_subset['gwp_Area_max_km2'] * 100

    # Calculate the max for each GLAKES_id
    glakes_subset['li_max_area'] = glakes_subset.groupby('GLAKES_id')['li_lake_surface_area_km2'].transform('max')
    #glakes_subset = glakes_subset[glakes_subset['li_max_area'] > 0.0].copy()

    #glakes_subset['validation-water-perc_glakes'] = glakes_subset['li_lake_surface_area_km2'] / glakes_subset['glakes_area'] * 100
    glakes_subset['validation-water-perc_li'] = glakes_subset['li_lake_surface_area_km2'] * 100 / glakes_subset['li_max_area'] 

    glakes_subset = glakes_subset.rename(columns ={
        "Date": "Date",
        "GLAKES_id": "GLAKES_id",
        "Hylak_id": "Hylak_id", 
        'GWP_lake_surface_area': 'gwp-water-km2',
        'li_lake_surface_area_km2': 'li-water-km2',
        #'validation-water-perc_glakes': 'validation-water-perc-glakes',
        'validation-water-perc_li': 'validation-water-perc-li',
        'latitude': 'Latitude',
        'longitude': 'Longitude',
        'li_max_area': 'li-max-area',
        'glakes_area': 'glakes-max-area',
        'gwp_Area_max_km2': 'gwp-max-area-wrong',
        "gwp-max-area-km2": "gwp-max-area-km2",
        "gwp-water-perc": "gwp-water-perc"})



    glakes_subset.describe()
    from scipy.stats import zscore
    # calculate z transformed values of all timeseries  
    glakes_z = glakes_subset.copy()
    glakes_z['zscore-gwp-perc'] = zscore(glakes_z['gwp-water-perc'])
    glakes_z['zscore-validation-water-perc-li'] = zscore(glakes_z['validation-water-perc-li'])
    #glakes_z['zscore-validation-water-perc-glakes'] = zscore(glakes_z['validation-water-perc-glakes'])
    glakes_z['zscore-gwp-area-km2'] = zscore(glakes_z['gwp-water-km2'])
    glakes_z['zscore-li-water-km2'] = zscore(glakes_z['li-water-km2'])

    #glakes_z.to_csv(OUTPUT_DIR / "glakes_z.csv", index=False)

    arlie_z = arlie_subset.copy()
    arlie_z['zscore-gwp-perc'] = zscore(arlie_z['gwp-water-perc'])
    arlie_z['zscore-validation-water-perc'] = zscore(arlie_z['validation-water-perc'])
    arlie_z['zscore-gwp-area-km2'] = zscore(arlie_z['gwp-area-km2'])

    nasaflood_z = nasaflood_subset.copy()
    nasaflood_z['zscore-gwp-perc'] = zscore(nasaflood_z['gwp-water-perc'])
    nasaflood_z['zscore-validation-water-perc'] = zscore(nasaflood_z['validation-water-perc']) 



    arlie_dict = {f"Lake_{hylak_id}": group.copy() for hylak_id, group in arlie_z.groupby('Hylak_id')}
    nasa_dict = {f"Lake_{hylak_id}": group.copy() for hylak_id, group in nasaflood_z.groupby('Hylak_id')}
    li_dict = {f"Lake_{GLAKES_id}": group.copy() for GLAKES_id, group in glakes_z.groupby('GLAKES_id')}

    for name,df in arlie_dict.items():
        if not {"gwp-water-perc-of-max", "validation-water-perc"}.issubset(df.columns):
            print(f"⚠️ {name} missing correct percentage columns")
        else:
            gwp_max = df["gwp-water-perc-of-max"].max()
            val_max = df["validation-water-perc"].max()
            if gwp_max > 100 or val_max > 100:
                print(f"⚠️ {name}: gwp max={gwp_max}, val max={val_max}")
    for name, df in nasa_dict.items():
        if not {"gwp-water-perc", "validation-water-perc"}.issubset(df.columns):
            print(f"⚠️ {name} missing correct percentage columns")
        else:
            gwp_max = df["gwp-water-perc"].max()
            val_max = df["validation-water-perc"].max()
            if gwp_max > 100 or val_max > 100:
                print(f"⚠️ {name}: gwp max={gwp_max}, val max={val_max}")
    for name, df in li_dict.items():
        if not {"gwp-water-perc", "validation-water-perc-li"}.issubset(df.columns):
            print(f"⚠️ {name} missing correct percentage columns")
        else:
            gwp_max = df["gwp-water-perc"].max()
            val_max = df["validation-water-perc-li"].max()
            if gwp_max > 100 or val_max > 100:
                print(f"⚠️ {name}: gwp max={gwp_max}, val max={val_max}")
    arl_sample_dfs, arl_constant_array_lakes, arlie_stats_df_z = calculate_stats_per_lake(arlie_dict, gwp_column = "zscore-gwp-area-km2", validation_column = "zscore-validation-water-perc", number_of_samples=arlie_number_of_sample, use_zscore=True)
    nasa_sample_dfs, nasa_constant_array_lakes, nasa_stats_df_z = calculate_stats_per_lake(nasa_dict, gwp_column = "zscore-gwp-perc", validation_column = "zscore-validation-water-perc", number_of_samples=nasaflood_number_of_sample, use_zscore=True)
    li_sample_dfs, li_constant_array_lakes, li_stats_df_z = calculate_stats_per_lake(li_dict, gwp_column = "zscore-gwp-area-km2", validation_column = "zscore-li-water-km2", number_of_samples=li_number_of_sample, use_zscore=True)


    arlie_stats_df_z['Dataset'] = 'Arlie'
    nasa_stats_df_z['Dataset'] = 'NASAFlood'
    li_stats_df_z['Dataset'] = 'Li'



    arl_sample_dfs, arl_constant_array_lakes, arlie_stats_df = calculate_stats_per_lake(arlie_dict, gwp_column = "gwp-water-perc-of-max", validation_column = "validation-water-perc", number_of_samples=arlie_number_of_sample, use_zscore=False)
    nasa_sample_dfs, nasa_constant_array_lakes, nasa_stats_df = calculate_stats_per_lake(nasa_dict, gwp_column = "gwp-water-perc", validation_column = "validation-water-perc", number_of_samples=nasaflood_number_of_sample, use_zscore=False)
    li_sample_dfs, li_constant_array_lakes, li_stats_df = calculate_stats_per_lake(li_dict, gwp_column = "gwp-water-perc", validation_column = "validation-water-perc-li", number_of_samples=li_number_of_sample, use_zscore=False)

    arlie_stats_df['Dataset'] = 'Arlie'
    nasa_stats_df['Dataset'] = 'NASAFlood'  
    li_stats_df['Dataset'] = 'Li'



    # save results
    arlie_stats_df_z.to_csv(OUTPUT_DIR / "arlie_stats_df_z.csv", index=False)
    nasa_stats_df_z.to_csv(OUTPUT_DIR / "nasa_stats_df_z.csv", index=False)
    li_stats_df_z.to_csv(OUTPUT_DIR / "li_stats_df_z.csv", index=False)

    # save results
    arlie_stats_df.to_csv(OUTPUT_DIR / "arlie_stats_df.csv", index=False)
    nasa_stats_df.to_csv(OUTPUT_DIR / "nasa_stats_df.csv", index=False)
    li_stats_df.to_csv(OUTPUT_DIR / "li_stats_df.csv", index=False)


    # make one long dataframe with all stats
    all_stats_df = pd.concat([arlie_stats_df, nasa_stats_df, li_stats_df])
    all_stats_df['value-type'] = 'water-perc'
    all_stats_df_z = pd.concat([arlie_stats_df_z, nasa_stats_df_z, li_stats_df_z])
    all_stats_df_z['value-type'] = 'water-zscore'

    all_stats = pd.concat([all_stats_df, all_stats_df_z])
    all_stats.to_csv(OUTPUT_DIR / "all_stats_df.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="calculate Statistics")
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

