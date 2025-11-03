
import pandas as pd
from pathlib import Path
import numpy as np
import geopandas as gpd
from globallakevariability.stats.statistics import calculate_stats_per_lake 
import os
import argparse
import json
from scipy.stats import zscore


def main(config):
    from scipy.stats import zscore
    import pandas as pd
    from pathlib import Path
    import numpy as np
    import geopandas as gpd
    from globallakevariability.stats.statistics import calculate_stats_per_lake 
    import os

    arlie_number_of_sample = config["stats"]["arlie_number_of_sample"]
    nasaflood_number_of_sample = config["stats"]["nasaflood_number_of_sample"]
    li_number_of_sample = config["stats"]["li_number_of_sample"]

    ROOT = Path(config['root'])
    li_path_strict = ROOT / config["input"]["li_data_strict"]
    li_path_no_frozen = ROOT / config["input"]["li_data_no_frozen"]
    arlie_path = ROOT / config["input"]["arlie_data"]
    nasa_path = ROOT / config["input"]["nasaflood_data"]
    hydrolakes = ROOT / config["input"]["hydrolakes"]
    OUTPUT_DIR = ROOT / config['output']["dir"]
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    glakes = pd.read_csv( li_path_strict, sep=',') 
    glakes_no_frozen = pd.read_csv( li_path_no_frozen, sep=',') 
    arlie = pd.read_csv (arlie_path, sep=',')
    nasaflood = pd.read_csv(nasa_path , sep=',')




    # create a safe copy of the subset to avoid SettingWithCopyWarning
    arlie_subset = arlie[["date", "Hylak_id", "water_perc", "Latitude", "Longitude", "GWP_Area"]].copy()

    # ensure numeric and avoid inf / non-numeric issues
    arlie_subset["GWP_Area"] = pd.to_numeric(arlie_subset["GWP_Area"], errors="coerce")
    arlie_subset["water_perc"] = pd.to_numeric(arlie_subset["water_perc"], errors="coerce")

    # compute per-lake max and percentage using .loc to avoid chained-assignment warnings
    arlie_subset.loc[:, "gwp-max-area-km2"] = arlie_subset.groupby("Hylak_id")["GWP_Area"].transform("max")
    # guard against division by zero / non-finite values
    arlie_subset.loc[:, "gwp-water-perc"] = (arlie_subset["GWP_Area"] * 100) / arlie_subset["gwp-max-area-km2"]
    arlie_subset.loc[:, "gwp-water-perc"].replace([np.inf, -np.inf], np.nan, inplace=True)

    # rename original columns (keep already computed gwp-water-perc)
    arlie_subset = arlie_subset.rename(columns={
        "date": "Date",
        "water_perc": "validation-water-perc",
        "GWP_Area": "gwp-area-km2"
    }).copy()

    # convert computed columns to numeric and clean infs/NaNs prior to zscore
    arlie_subset["gwp-area-km2"] = pd.to_numeric(arlie_subset["gwp-area-km2"], errors="coerce")
    arlie_subset["gwp-water-perc"] = pd.to_numeric(arlie_subset["gwp-water-perc"], errors="coerce")
    arlie_subset["validation-water-perc"] = pd.to_numeric(arlie_subset["validation-water-perc"], errors="coerce")

    # compute z-scores with pandas (skip NaN automatically)
    def safe_zscore(series):
        if series.dropna().size == 0:
            return pd.Series([np.nan] * len(series), index=series.index)
        mean = series.mean(skipna=True)
        std = series.std(ddof=0, skipna=True)
        if std == 0 or np.isnan(std):
            return pd.Series([np.nan] * len(series), index=series.index)
        return (series - mean) / std

    arlie_z = arlie_subset.copy()
    arlie_z["zscore-gwp-perc"] = safe_zscore(arlie_z["gwp-water-perc"])
    arlie_z["zscore-validation-water-perc"] = safe_zscore(arlie_z["validation-water-perc"])
    arlie_z["zscore-gwp-area-km2"] = safe_zscore(arlie_z["gwp-area-km2"])



    arlie_dict = {f"Lake_{hylak_id}": group.copy() for hylak_id, group in arlie_z.groupby('Hylak_id')}

    for name,df in arlie_dict.items():
        if not {"gwp-water-perc", "validation-water-perc"}.issubset(df.columns):
            print(f"⚠️ {name} missing correct percentage columns")
        else:
            gwp_max = df["gwp-water-perc"].max()
            val_max = df["validation-water-perc"].max()
            if gwp_max > 100 or val_max > 100:
                print(f"⚠️ {name}: gwp max={gwp_max}, val max={val_max}")


    
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
    glakes_subset_no_frozen = glakes_no_frozen[["Date", "GLAKES_id", "Hylak_id", "GWP_lake_surface_area", "gwp_Area_max_km2", "li_lake_surface_area_km2", "latitude", "longitude", "glakes_area"]].copy()
    
    # Process glakes_subset (strict)
    glakes_subset['gwp-max-area-km2'] = glakes_subset['GWP_lake_surface_area'].groupby(glakes_subset['GLAKES_id']).transform("max")
    glakes_subset['gwp-water-perc'] = glakes_subset['GWP_lake_surface_area'] / glakes_subset['gwp-max-area-km2'] * 100
    glakes_subset['li_max_area'] = glakes_subset.groupby('GLAKES_id')['li_lake_surface_area_km2'].transform('max')
    glakes_subset['validation-water-perc_li'] = glakes_subset['li_lake_surface_area_km2'] * 100 / glakes_subset['li_max_area'] 

    glakes_subset = glakes_subset.rename(columns ={
        "Date": "Date",
        "GLAKES_id": "GLAKES_id",
        "Hylak_id": "Hylak_id", 
        'GWP_lake_surface_area': 'gwp-water-km2',
        'li_lake_surface_area_km2': 'li-water-km2',
        'validation-water-perc_li': 'validation-water-perc-li',
        'latitude': 'Latitude',
        'longitude': 'Longitude',
        'li_max_area': 'li-max-area',
        'glakes_area': 'glakes-max-area',
        'gwp_Area_max_km2': 'gwp-max-area-wrong',
        "gwp-max-area-km2": "gwp-max-area-km2",
        "gwp-water-perc": "gwp-water-perc"})

    # Process glakes_subset_no_frozen (same steps)
    glakes_subset_no_frozen['gwp-max-area-km2'] = glakes_subset_no_frozen['GWP_lake_surface_area'].groupby(glakes_subset_no_frozen['GLAKES_id']).transform("max")
    glakes_subset_no_frozen['gwp-water-perc'] = glakes_subset_no_frozen['GWP_lake_surface_area'] / glakes_subset_no_frozen['gwp-max-area-km2'] * 100
    glakes_subset_no_frozen['li_max_area'] = glakes_subset_no_frozen.groupby('GLAKES_id')['li_lake_surface_area_km2'].transform('max')
    glakes_subset_no_frozen['validation-water-perc_li'] = glakes_subset_no_frozen['li_lake_surface_area_km2'] * 100 / glakes_subset_no_frozen['li_max_area'] 

    glakes_subset_no_frozen = glakes_subset_no_frozen.rename(columns ={
        "Date": "Date",
        "GLAKES_id": "GLAKES_id",
        "Hylak_id": "Hylak_id", 
        'GWP_lake_surface_area': 'gwp-water-km2',
        'li_lake_surface_area_km2': 'li-water-km2',
        'validation-water-perc_li': 'validation-water-perc-li',
        'latitude': 'Latitude',
        'longitude': 'Longitude',
        'li_max_area': 'li-max-area',
        'glakes_area': 'glakes-max-area',
        'gwp_Area_max_km2': 'gwp-max-area-wrong',
        "gwp-max-area-km2": "gwp-max-area-km2",
        "gwp-water-perc": "gwp-water-perc"})


    # Z-score transformation for glakes_subset (strict)
    glakes_z = glakes_subset.copy()
    glakes_z['zscore-gwp-perc'] = zscore(glakes_z['gwp-water-perc'])
    glakes_z['zscore-validation-water-perc-li'] = zscore(glakes_z['validation-water-perc-li'])
    glakes_z['zscore-gwp-area-km2'] = zscore(glakes_z['gwp-water-km2'])
    glakes_z['zscore-li-water-km2'] = zscore(glakes_z['li-water-km2'])

    # Z-score transformation for glakes_subset_no_frozen
    glakes_z_no_frozen = glakes_subset_no_frozen.copy()
    glakes_z_no_frozen['zscore-gwp-perc'] = zscore(glakes_z_no_frozen['gwp-water-perc'])
    glakes_z_no_frozen['zscore-validation-water-perc-li'] = zscore(glakes_z_no_frozen['validation-water-perc-li'])
    glakes_z_no_frozen['zscore-gwp-area-km2'] = zscore(glakes_z_no_frozen['gwp-water-km2'])
    glakes_z_no_frozen['zscore-li-water-km2'] = zscore(glakes_z_no_frozen['li-water-km2'])

    nasaflood_z = nasaflood_subset.copy()
    nasaflood_z['zscore-gwp-perc'] = zscore(nasaflood_z['gwp-water-perc'])
    nasaflood_z['zscore-validation-water-perc'] = zscore(nasaflood_z['validation-water-perc']) 


    nasa_dict = {f"Lake_{hylak_id}": group.copy() for hylak_id, group in nasaflood_z.groupby('Hylak_id')}
    li_dict = {f"Lake_{GLAKES_id}": group.copy() for GLAKES_id, group in glakes_z.groupby('GLAKES_id')}
    li_dict_no_frozen = {f"Lake_{GLAKES_id}": group.copy() for GLAKES_id, group in glakes_z_no_frozen.groupby('GLAKES_id')}

    
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
    
    for name, df in li_dict_no_frozen.items():
        if not {"gwp-water-perc", "validation-water-perc-li"}.issubset(df.columns):
            print(f"⚠️ {name} (no_frozen) missing correct percentage columns")
        else:
            gwp_max = df["gwp-water-perc"].max()
            val_max = df["validation-water-perc-li"].max()
            if gwp_max > 100 or val_max > 100:
                print(f"⚠️ {name} (no_frozen): gwp max={gwp_max}, val max={val_max}")

    # Find the shortest dataframe length in each dictionary
    min_length_arlie = min([len(df) for df in arlie_dict.values()])
    min_length_nasa = min([len(df) for df in nasa_dict.values()])
    min_length_li = min([len(df) for df in li_dict.values()])
    min_length_li_no_frozen = min([len(df) for df in li_dict_no_frozen.values()])

    print(f"Minimum length of Arlie dataframes: {min_length_arlie}")
    print(f"Minimum length of NASAFlood dataframes: {min_length_nasa}")
    print(f"Minimum length of Li dataframes: {min_length_li}")
    print(f"Minimum length of Li (no frozen) dataframes: {min_length_li_no_frozen}")
    
    # Calculate stats with z-scores
    arl_sample_dfs, arl_constant_array_lakes, arlie_stats_df_z = calculate_stats_per_lake(arlie_dict, gwp_column = "zscore-gwp-area-km2", validation_column = "zscore-validation-water-perc", number_of_samples=min_length_arlie, use_zscore=True)
    nasa_sample_dfs, nasa_constant_array_lakes, nasa_stats_df_z = calculate_stats_per_lake(nasa_dict, gwp_column = "zscore-gwp-perc", validation_column = "zscore-validation-water-perc", number_of_samples=min_length_nasa, use_zscore=True)
    li_sample_dfs, li_constant_array_lakes, li_stats_df_z = calculate_stats_per_lake(li_dict, gwp_column = "zscore-gwp-area-km2", validation_column = "zscore-li-water-km2", number_of_samples=min_length_li, use_zscore=True)
    li_sample_dfs_no_frozen, li_constant_array_lakes_no_frozen, li_stats_df_z_no_frozen = calculate_stats_per_lake(li_dict_no_frozen, gwp_column = "zscore-gwp-area-km2", validation_column = "zscore-li-water-km2", number_of_samples=min_length_li_no_frozen, use_zscore=True)

    arlie_stats_df_z['Dataset'] = 'Arlie'
    nasa_stats_df_z['Dataset'] = 'NASAFlood'
    li_stats_df_z['Dataset'] = 'Li'
    li_stats_df_z_no_frozen['Dataset'] = 'Li_no_frozen'

    # Calculate stats without z-scores
    arl_sample_dfs, arl_constant_array_lakes, arlie_stats_df = calculate_stats_per_lake(arlie_dict, gwp_column = "gwp-water-perc", validation_column = "validation-water-perc", number_of_samples=min_length_arlie, use_zscore=False)
    nasa_sample_dfs, nasa_constant_array_lakes, nasa_stats_df = calculate_stats_per_lake(nasa_dict, gwp_column = "gwp-water-perc", validation_column = "validation-water-perc", number_of_samples=min_length_nasa, use_zscore=False)
    li_sample_dfs, li_constant_array_lakes, li_stats_df = calculate_stats_per_lake(li_dict, gwp_column = "gwp-water-perc", validation_column = "validation-water-perc-li", number_of_samples=min_length_li, use_zscore=False)
    li_sample_dfs_no_frozen, li_constant_array_lakes_no_frozen, li_stats_df_no_frozen = calculate_stats_per_lake(li_dict_no_frozen, gwp_column = "gwp-water-perc", validation_column = "validation-water-perc-li", number_of_samples=min_length_li_no_frozen, use_zscore=False)

    arlie_stats_df['Dataset'] = 'Arlie'
    nasa_stats_df['Dataset'] = 'NASAFlood'  
    li_stats_df['Dataset'] = 'Li'
    li_stats_df_no_frozen['Dataset'] = 'Li_no_frozen'

    # Save results
    arlie_stats_df_z.to_csv(OUTPUT_DIR / "arlie_stats_df_z.csv", index=False)
    nasa_stats_df_z.to_csv(OUTPUT_DIR / "nasa_stats_df_z.csv", index=False)
    li_stats_df_z.to_csv(OUTPUT_DIR / "li_stats_df_z.csv", index=False)
    li_stats_df_z_no_frozen.to_csv(OUTPUT_DIR / "li_stats_df_z_no_frozen.csv", index=False)

    arlie_stats_df.to_csv(OUTPUT_DIR / "arlie_stats_df.csv", index=False)
    nasa_stats_df.to_csv(OUTPUT_DIR / "nasa_stats_df.csv", index=False)
    li_stats_df.to_csv(OUTPUT_DIR / "li_stats_df.csv", index=False)
    li_stats_df_no_frozen.to_csv(OUTPUT_DIR / "li_stats_df_no_frozen.csv", index=False)

    # Make one long dataframe with all stats
    all_stats_df = pd.concat([arlie_stats_df, nasa_stats_df, li_stats_df, li_stats_df_no_frozen])
    all_stats_df['value-type'] = 'Area-perc'

    all_stats_df_z = pd.concat([arlie_stats_df_z, nasa_stats_df_z, li_stats_df_z, li_stats_df_z_no_frozen])
    all_stats_df_z['value-type'] = 'Area-normalized'

    # Rename _z columns (remove _z suffix)
    all_stats_df_z.columns = all_stats_df_z.columns.str.replace('_z', '')

    # Combine both DataFrames
    all_stats_combined = pd.concat([all_stats_df, all_stats_df_z], ignore_index=True)

    print(f"Total rows: {len(all_stats_combined)}")
    print(f"Value types:\n{all_stats_combined['value-type'].value_counts()}") 

    all_stats_combined.to_csv(OUTPUT_DIR / "all_stats_df.csv", index=False)
    print(all_stats_combined.head())
    
    summary_compact = all_stats_combined.groupby(['Dataset', 'value-type']).agg({
        'RMSE': ['mean', 'std', 'median', 'min', 'max'],
        'spearman_cor': ['mean', 'std', 'median', 'min', 'max'],
        'Hylak_id': 'count',
        'Dataset': 'first',
        'value-type': 'first'
    }).round(4)

    summary_compact.columns = ['_'.join(col).strip() for col in summary_compact.columns.values]
    summary_compact.rename(columns={'Hylak_id_count': 'n_lakes'}, inplace=True)
    print(summary_compact)
    summary_compact.to_csv(OUTPUT_DIR / "stats_summary_compact.csv", index=False)



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