import pandas as pd
from pathlib import Path
import geopandas as gpd
import json
import argparse
from globallakevariability.preprocessing.zonal_statistics import apply_area_deviation_check
# Define Paths and variables


def apply_disruption_threshold(df, disruption_threshold=10):
    filtered_df = df[df['mwp-insufficientData-perc'] <= disruption_threshold]
    return filtered_df

def main(config):

    disruption_threshold = config['matching']['disruption_threshold']
    minimum_length_of_dataframes = config['matching']['minimum_length_to_keep_df']
    maximum_area_difference = config['matching']['maximum_area_difference']

    ROOT = Path(config["root_dir"])
    lakes_df = ROOT / config["zonal_statistics"]["output"] / "all_lakes_combined.csv"
    hydrolakes = ROOT / config['preprocessing']['output_dir_hydrolakes'] / config['matching']['gwp_hydrolakes_max_extent']
    OUTPUT_ROOT = ROOT / Path(config["matching"]["output_directory"])


    # drop number after comma in disruption threshold
    disruption_threshold_filename = int(disruption_threshold * 100)
    excelfile = OUTPUT_ROOT / f"all_lakes_percentage_{disruption_threshold_filename}percDisr.xlsx"
    csvfile = OUTPUT_ROOT / f"all_lakes_percentage_{disruption_threshold_filename}percDisr.csv"


    ''' 
    Preparations:
    1. there are still no-Data Values inside the dataframe - those will be saved as 0 -> Define a vector with all columns that need to be processed
    2. Create a dictionary based on the Hylak Id containg dataframes for each lake
    3. Group the dataframes within the dictionary by date 
    4. Calculate the Area in percentage
    5. Remove all lakes smaller then 20m²
    6. Check for Area differences of more then 10% between MWP and GWP 
    7. Disruption filter - based on the disruption theshold defined above
    8. Length filter - based on the minimum length for dataframes defined above
    9. Add all available GWP coordinates to the lakes
    10. Save the Datasets
    '''

    # Step 1
    all_lakes_df = pd.read_csv(lakes_df)
    to_na_all_lakes = [ 'mwp-count', 
                       'mwp-insufficientData', 
                       'mwp-noWater',
                       'mwp-surfaceWater',
                       'mwp-Flood', 
                       'gwp-Water',
        'gwp-noWater', 'gwp-count']
    print(all_lakes_df.columns)
    all_lakes_df[to_na_all_lakes] = all_lakes_df[to_na_all_lakes].fillna(0)


    # Step 2
    hylak_ids = all_lakes_df['Hylak_id'].unique()

    lakes_dict = {f"Lake_{hylak_id}": group.copy() for hylak_id, group in all_lakes_df.groupby('Hylak_id')}
    print(f"Included in the MWP-Tiles are: {len(lakes_dict.keys())} lakes")


    # Step 3 + 4
    grouped_dict = {}

    for key, value in lakes_dict.items():

        value['date'] = pd.to_datetime(value['date'])

        df_grouped = value.groupby("date").agg({'Hylak_id':"first", 'Lake_name':"first", 'Country':"first", 'Continent':"first", 'Lake_area': "sum",
        'Area_max':"sum", 'mwp-insufficientData':"sum", 'mwp-noWater':"sum", 'mwp-surfaceWater':"sum",
        'mwp-Flood': "sum", 'mwp-count': "sum", 'year': "first", 'doy': "first", 'gwp-noWater': "sum",
        'gwp-Water': "sum", 'gwp-count': "sum", 'tile':"first", 'date': "first"})

        df_grouped['mwp-insufficientData-perc'] = df_grouped['mwp-insufficientData']*100 / df_grouped['mwp-count']
        df_grouped['mwp-noWater-perc'] = df_grouped['mwp-noWater']*100 / df_grouped['mwp-count']
        df_grouped['mwp_totalWater'] =  (df_grouped['mwp-surfaceWater'] + df_grouped['mwp-Flood'])
        df_grouped['mwp-total-water-perc'] = (df_grouped['mwp-surfaceWater'] + df_grouped['mwp-Flood'])*100 / df_grouped['mwp-count']
        df_grouped['gwp-water-perc'] = df_grouped['gwp-Water']*100 / df_grouped['gwp-count']
        df_grouped['gwp-no-water-perc'] = df_grouped['gwp-noWater']*100 / df_grouped['gwp-count']
        grouped_dict[key] = df_grouped

    # Step 5
    deviation_issues = []
    lakes_smaller_20 = []


    filtered_dict = {}

    removed_lakes = 0


    for lake, df in grouped_dict.items():

        min_lake_area = 20 # lake area must be minimum of 20km²

        if 'Lake_area' in df.columns and df['Lake_area'].iloc[0] > min_lake_area:
            filtered_dict[lake] = df
        else: 
            lakes_smaller_20.append(f"{lake} removed because smaller then 20km²")
            removed_lakes +=1
    print(f"removed {removed_lakes} lakes, because they were smaller then 20km².")
        
    print(f"We know have a total of {len(filtered_dict.items())} lakes.")

    # Step 6
    import numpy as np
    from tqdm import tqdm


    area_consistent_dict = {}
    area_inconsistent_data = []

    for lake_id, df in tqdm(filtered_dict.items(), desc='Area Consistency Check'):
        clean_df, removed_df = apply_area_deviation_check(df, max_area_difference=maximum_area_difference)
        
        if len(clean_df) > 0:
            area_consistent_dict[lake_id] = clean_df
        
        # Statistiken sammeln
        if len(removed_df) > 0:
            area_inconsistent_data.append({
                'Hylak_id': lake_id,
                'Lake_name': df['Lake_name'].iloc[0],
                'total_points': len(df),
                'removed_points': len(removed_df),
                'max_deviation': df['pixel_deviation'].max(),
                'avg_deviation': df['pixel_deviation'].mean()
            })

    # Ergebnisse
    print(f"Seen vor Area Check: {len(filtered_dict)}")
    print(f"Seen nach Area Check: {len(area_consistent_dict)}")
    print(f"Seen mit inkonsistenten Datenpunkten: {len(area_inconsistent_data)}")
    from globallakevariability.utils.helper import find_min_max_length


    # Step 7 
    no_disruption_dict = {}
    completely_removed_lakes = []

    for lake_id, df in tqdm(filtered_dict.items(), desc='Disruption Threshold Check'):
        filtered_df = apply_disruption_threshold(df, disruption_threshold=disruption_threshold)
        
        if len(filtered_df) > 0:
            no_disruption_dict[lake_id] = filtered_df
        else:
            # See wird komplett entfernt - explizit dokumentieren
            completely_removed_lakes.append({
                'Hylak_id': lake_id,
                'Lake_name': df['Lake_name'].iloc[0],
                'Lake_area': df['Lake_area'].iloc[0],
                'total_points': len(df),
                'reason': 'All data points above disruption threshold',
                'avg_insufficient_data_perc': df['mwp-insufficientData-perc'].mean()
            })

    # Ergebnisse nach Disruption Check
    print(f"Seen vor Disruption Check: {len(filtered_dict)}")
    print(f"Seen nach Disruption Check: {len(no_disruption_dict)}")
    print(f"Komplett entfernte Seen (Disruption): {len(completely_removed_lakes)}")

    # Zeige entfernte Seen
    if completely_removed_lakes:
        removed_df = pd.DataFrame(completely_removed_lakes)
        print(f"\nEntfernte Seen (Disruption):\n{removed_df[['Lake_name', 'Lake_area', 'avg_insufficient_data_perc']]}")

    print("\n" + "="*minimum_length_of_dataframes)

    # Step 8
    print("Überprüfung der Mindestanzahl von Datenpunkten...")
    min_length, max_length, final_cleaned_dict, length_stats = find_min_max_length(
        no_disruption_dict, 
        min_length_to_keep_df=minimum_length_of_dataframes
    )

    # Dokumentiere zusätzlich entfernte Seen (wegen zu wenig Datenpunkte)
    length_removed_lakes = []
    for lake_id in no_disruption_dict.keys():
        if lake_id not in final_cleaned_dict:
            df = no_disruption_dict[lake_id]
            length_removed_lakes.append({
                'Hylak_id': lake_id,
                'Lake_name': df['Lake_name'].iloc[0],
                'Lake_area': df['Lake_area'].iloc[0],
                'total_points': len(df),
                'reason': f'Insufficient data points (< {minimum_length_of_dataframes})',
                'actual_points': len(df)
            })

    print(f"\nZusätzlich entfernte Seen (< {minimum_length_of_dataframes} Datenpunkte): {len(length_removed_lakes)}")
    if length_removed_lakes:
        length_removed_df = pd.DataFrame(length_removed_lakes)
        print(f"Entfernte Seen (< {minimum_length_of_dataframes} Punkte):\n{length_removed_df[['Lake_name', 'Lake_area', 'actual_points']]}")

    # Finale Statistiken
    print("\n" + "="*minimum_length_of_dataframes)
    print("FINALE STATISTIKEN:")
    print(f"Ursprüngliche Anzahl Seen: {len(filtered_dict)}")
    print(f"Nach Disruption-Filterung: {len(no_disruption_dict)}")
    print(f"Nach Mindestpunkt-Filterung: {len(final_cleaned_dict)}")
    print(f"Gesamt entfernte Seen: {len(completely_removed_lakes) + len(length_removed_lakes)}")

    if final_cleaned_dict:
        print(f"Finale Datenpunkt-Range: {min_length} bis {max_length}")
        
        # Zeige Verteilung der finalen Datenpunkte
        final_lengths = [len(df) for df in final_cleaned_dict.values()]
        print(f"Durchschnittliche Datenpunkte pro See: {np.mean(final_lengths):.1f}")
        print(f"Median Datenpunkte pro See: {np.median(final_lengths):.1f}")

    # Kombiniere alle entfernten Seen für finale Dokumentation
    all_removed_lakes = completely_removed_lakes + length_removed_lakes
    if all_removed_lakes:
        all_removed_df = pd.DataFrame(all_removed_lakes)
        print(f"\nGesamte entfernte Seen: {len(all_removed_df)}")
        
        # Gruppiere nach Grund der Entfernung
        removal_reasons = all_removed_df['reason'].value_counts()
        print("Gründe für Entfernung:")
        for reason, count in removal_reasons.items():
            print(f"  - {reason}: {count} Seen")

    # Das finale Dictionary verwenden
    print(f"\nFinales Dictionary 'final_cleaned_dict' enthält {len(final_cleaned_dict)} Seen")
    print("Bereit für weitere Analyse!")

    # Step 9

    hydrolakes = gpd.read_file(hydrolakes)
    hydrolakes.columns
    coordinates_df = hydrolakes[['latitude', 'longitude', 'Hylak_id']].drop_duplicates(subset='Hylak_id').reset_index(drop=True)
    coordinates_df['Hylak_id'] = coordinates_df['Hylak_id'].astype("float64")
    # Füge 'Lake_' Präfix hinzu und erstelle das Dictionary
    coordinates_df['Lake_Hylak_id'] = 'Lake_' + coordinates_df['Hylak_id'].astype(str)
    lat_lon_dict = coordinates_df.set_index('Lake_Hylak_id')[['latitude', 'longitude']].to_dict(orient='index')

    for key, value in final_cleaned_dict.items():
        hylak_id = value['Hylak_id'].iloc[0]
        lake_key = f"Lake_{hylak_id}"

        if lake_key in lat_lon_dict:
            latitude, longitude = lat_lon_dict[lake_key]['latitude'], lat_lon_dict[lake_key]['longitude']
            df = final_cleaned_dict[key].copy()
            df['latitude'] = latitude
            df['longitude'] = longitude
            final_cleaned_dict[key] = df

        #   final_cleaned_dict[key].loc[:, 'latitude'] = latitude
        #   final_cleaned_dict[key].loc[:, 'longitude'] = longitude

        print(f"Number of lakes after adding coordinates: {len(final_cleaned_dict.items())} ")
    # # Überprüfe, ob die latitude und longitude zu filtered_dict hinzugefügt wurden
    # print("Spalten nach dem Hinzufügen:")
    # for key in final_cleaned_dict:
    #     print(f"Key: {key}, Spalten: {filtered_dict[key].columns.tolist()}")

    # Step 10

    final_df = pd.concat(final_cleaned_dict.values())
    final_df.to_csv(csvfile)
    final_df.to_excel(excelfile, float_format="%.6f", index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="match GWP with NasaFloodProduct")
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

