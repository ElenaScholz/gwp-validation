import argparse
import json
def main(config):
    import pandas as pd
    from pathlib import Path
    import geopandas as gpd

    import os

    ROOT = Path(config['root_dir'])
    INPUT_FILE =  ROOT / config['preprocessing']['monthly_li_lse'] 
    OUTPUT_FILE = ROOT / config['preprocessing']['monthly_li_long']
    NEEDED_IDS = gpd.read_file(ROOT / config['preprocessing']['prepared_glakes_ds'])
    


    NEEDED_IDS = NEEDED_IDS['Hylak_id'].unique() 

    df = pd.read_csv(INPUT_FILE)

    df = df[df['Hylak_id'].isin(NEEDED_IDS)]   


    # Angenommen, df_long ist wie vorher erzeugt
    # df_long: Hylak_id | month | lake_surface_area | frozen

    output_dir = ROOT / config['preprocessing']["li_monthly_lakes_dir"]
    os.makedirs(output_dir, exist_ok=True)  # Ordner anlegen, falls nicht existent
    import pandas as pd

    # assuming your dataframe is called df

    # 1. Identify columns
    date_cols = [col for col in df.columns if col.startswith("20")]        # monthly surface area columns
    frozen_cols = [col for col in df.columns if col.startswith("frozen_")] # frozen flag columns

    # 2. Melt surface area columns
    df_long = df.melt(id_vars=["Hylak_id"], value_vars=date_cols,
                    var_name="month", value_name="lake_surface_area")

    # 3. Melt frozen columns
    df_frozen = df.melt(id_vars=["Hylak_id"], value_vars=frozen_cols,
                        var_name="month", value_name="frozen")

    # 4. Align frozen month names to match surface area month names
    # remove "frozen_" prefix
    df_frozen["month"] = df_frozen["month"].str.replace("frozen_", "")

    # 5. Merge surface area and frozen flags
    df_long = df_long.merge(df_frozen, on=["Hylak_id", "month"])

    # 6. Optional: convert month to datetime
    df_long["month"] = pd.to_datetime(df_long["month"])

    # 7. Optional: create a dictionary of dataframes by Hylak_id
    #dfs_by_hylak = {hid: g for hid, g in df_long.groupby("Hylak_id")}

    df_long.to_csv(OUTPUT_FILE, index=False)

    # Schreibe jede Hylak_id einzeln
    for hid, group in df_long.groupby("Hylak_id"):
        filename = os.path.join(output_dir, f"Hylak_{hid}.csv")
        group.to_csv(filename, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="reshape monthly Li LSE data to long format")
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
