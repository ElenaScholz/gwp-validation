import os
import re
from pathlib import Path
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely import wkt

class ArlieProcessor:
    def __init__(self,
                 root_to_arlie_folder: str,
                 path_to_hylak_dataset: str,
                 gwp_dataset_with_hylak_ids # # dataframe that contains only the hylak ids and corresponding names of statistical gwp data
                 ):
        self.arlie_files = [Path(root_to_arlie_folder) / file for file in os.listdir(Path(root_to_arlie_folder))]
        self.hylak_dataset = gpd.read_file( path_to_hylak_dataset)
        self.gwp_with_hylak_id = gwp_dataset_with_hylak_ids
        self.gwp_arlie_dict = {}

        self.arlie_geometries = {}
        self.stats_dict = {}
        self.gwp_arlie_dicts = {}
        self.arlie_to_hylak = {}
        self.multiple_assignments = {}
    
    def prepareArlieGeometries(self): 
        '''Reads geometry files, removes rivers, filters small areas, and converts them into GeoDataFrames.'''
        for file in self.arlie_files:
            if file.name.endswith("geometries.csv"):
                match = re.search(r'\d{3}_geometries', file.name) 
                if not match:
                    continue  # Falls kein Match gefunden wird, weitergehen

                geometry = pd.read_csv(file, sep=";")
                if geometry.shape[0] == 0:  
                    print(f"⚠️ WARNING: file {file} contains only header and will not be used.")
                    continue

                if 'river_km' in geometry.columns: 
                    geometry_noRivers = geometry#[geometry["river_km"].isna()]
                    geometry_filtered = geometry_noRivers[
                        geometry_noRivers["geometry"].str.startswith(("POLYGON", "MULTIPOLYGON"), na=False) #&
                       # (geometry_noRivers["area"] > 5000000)  # remove areas smaller than 5 km²
                    ]

                    geometry_filtered = geometry_filtered.copy()
                    geometry_filtered["geometry"] = geometry_filtered["geometry"].apply(wkt.loads)  
                    gdf = gpd.GeoDataFrame(geometry_filtered, geometry="geometry", crs="EPSG:3035")  
                    gdf = gdf.to_crs("EPSG:4326")  

                    geom_id = match.group(0)[:-11]
                    self.arlie_geometries[geom_id] = gdf  # Speichert das Ergebnis für späteres Matching

        return self.arlie_geometries
    
    def apply_negative_buffer(self, buffer_distance=-0.0003):  # Für geographische Koordinaten
        """
        Wendet einen negativen Buffer auf die Arlie-Geometrien an, um kleine Überlappungen zu eliminieren.
        
        Args:
            buffer_distance: Negativer Bufferwert in den Einheiten der CRS
        """
        for geom_id, gdf in self.arlie_geometries.items():

            if gdf.empty:
                continue  # Überspringe leere Geometrien

            orig_crs = gdf.crs  # Ursprüngliche CRS speichern

            gdf['geometry'] = gdf.geometry.make_valid()

            centroid = gdf.union_all(method = "unary").centroid
            utm_zone = int(((centroid.x + 180) / 6) % 60) + 1
            projected_crs = f"EPSG:{32600 + utm_zone}" if centroid.y >= 0 else f"EPSG:{32700 + utm_zone}"
        
            # Erstelle kopie um Warnungen zu vermeiden
            gdf_copy = gdf.copy()
            # Konvertiere in UTM-Koordinaten
            gdf_projected = gdf_copy.to_crs(projected_crs)

            # Wende negativen Buffer an
            gdf_projected['geometry'] = gdf_projected.geometry.buffer(buffer_distance)
            
            # Zurück zum ursprünglichen CRS
            gdf_buffered = gdf_projected.to_crs(orig_crs)
        
            # Entferne leere Geometrien
            gdf_buffered = gdf_buffered[~gdf_buffered.geometry.is_empty]
            
        
            self.arlie_geometries[geom_id] = gdf_buffered  # Aktualisiere die Geometrien in der Liste
        
        return self.arlie_geometries
        
    def filter_by_overlap_threshold(self, threshold_percentage=10):
        """
        Filtert Arlie-Polygone basierend auf ihrem Überlappungsgrad mit HyLAK-Polygonen.
        
        Args:
            threshold_percentage: Minimaler Überlappungsprozentsatz (z.B. 10 für 10%)
        """
        filtered_geometries = {}
        
        for geom_id, arlie_gdf in self.arlie_geometries.items():
            # Liste zum Speichern der Polygone, die den Schwellenwert erfüllen
            valid_polygons = []
            
            for idx, arlie_row in arlie_gdf.iterrows():
                arlie_geom = arlie_row.geometry.buffer(0) # Repariere Geometrien
                arlie_area = arlie_geom.area
                
                # Finde potentielle Überlappungen durch räumliche Indexierung
                possible_matches_idx = self.hylak_dataset.sindex.query(arlie_geom)
                possible_matches = self.hylak_dataset.iloc[possible_matches_idx]
                #print(possible_matches)
                valid_match = False
                for _, hylak_row in possible_matches.iterrows():
                    hylak_geom = hylak_row.geometry
                    
                    # Berechne Überlappungsfläche
                    if arlie_geom.intersects(hylak_geom):
                        intersection_area = arlie_geom.intersection(hylak_geom).area
                        overlap_percentage = (intersection_area / arlie_area) * 100
                        
                        if overlap_percentage >= threshold_percentage:
                            valid_match = True
                            break
                
                if valid_match:
                    valid_polygons.append(arlie_row)
            
            if valid_polygons:
                filtered_geometries[geom_id] = gpd.GeoDataFrame(valid_polygons, crs=arlie_gdf.crs)
        
        # Ersetze die ursprünglichen Geometrien durch die gefilterten
        self.arlie_geometries = filtered_geometries
        return self.arlie_geometries
                        

    def matchArlieAndGWP(self):
        '''Matches Arlie geometries with GWP IDs and adds additional attributes.'''
        for geom_id, gdf in self.arlie_geometries.items():  # Iteriere über die vorher gespeicherten Geometrien
            
            
            if gdf.empty:
                print(f"⚠️ WARNING: No geometries found for {geom_id}. Skipping.")
                continue

            
            gdf = gpd.sjoin(gdf, self.hylak_dataset,  how="left", predicate="intersects")  # Führe den räumlichen Join durch	

           # gdf = gdf.dropna(subset=['basin_name'])  # Entferne Zeilen bei denen kein See zugeordnet werden konnte


            gdf['Lake_area_HyLak'] = gdf['Lake_area']
            gdf['Lake_name_HyLak'] = gdf['Lake_name']
            gdf.drop(columns=['index_right', 'Lake_name', 'eu_hydro_id', 'Lake_area'], inplace=True)

            #arlie_with_gwpId = gdf.merge(self.gwp_with_hylak_id, on="Hylak_id", how="left")
            gdf['Hylak_id'] = gdf['Hylak_id'].astype(str)
            self.gwp_with_hylak_id['Hylak_id'] = self.gwp_with_hylak_id['Hylak_id'].astype(str)
            arlie_with_gwpId = gdf.merge(self.gwp_with_hylak_id, on="Hylak_id", how="left")

            #print(arlie_with_gwpId.columns)
            arlie_with_gwpId = arlie_with_gwpId.dropna(subset=['gwp_id'])

            self.gwp_arlie_dict[geom_id] = arlie_with_gwpId  # Speichert das finale Mapping

        return self.gwp_arlie_dict
    
    
    def mergeArlieStatsWithGeoms(self):
                
        for file in self.arlie_files:
            if file.name.endswith("arlie.csv"):
                match = re.search(r'\d{3}_arlie', file.name) 
                if not match:
                    continue
                    
            
                arlie_id = match.group(0)[:-6]  # Entferne "_arlie"
                print(f"Verarbeite Arlie-Datei für ID: {arlie_id}")
                
                # Lade Arlie-Daten
                arlie = pd.read_csv(file, sep=";")

                
                # Filtere und konvertiere
                arlie = arlie[arlie['qc'] == 0]
                arlie = arlie.copy()
                arlie['river_km_id'] = arlie['river_km_id'].astype(str)
                
                # Suche entsprechende Geometrie-Daten
                if arlie_id in self.gwp_arlie_dict:
                    geom_gdf = self.gwp_arlie_dict[arlie_id]
                    geom_gdf['id'] = geom_gdf['id'].astype(str)
                    
                    # Führe den Merge durch (wie in deinem manuellen Beispiel)
                    merged_df = pd.merge(
                        arlie,              # df1 (arlie_stats)
                        geom_gdf,           # df2 (arlie_geometries)
                        left_on='river_km_id',
                        right_on='id'
                    )

                    merged_df.drop(columns =["id_x", "id_y", "basin_name", "river_km"], inplace=True)
                    
                    # Speichere das Ergebnis
                    self.stats_dict[arlie_id] = merged_df
                    #print(f"Erfolgreich gemergt: {arlie_id} mit {len(merged_df)} Zeilen")
                else:
                    print(f"Keine entsprechenden Geometriedaten für ID: {arlie_id} gefunden")
   
        return self.stats_dict
    
    def save_dict(self, data_dict, output_path):

        output_path = Path(output_path)

        os.makedirs(output_path, exist_ok=True)

        for lake, df in data_dict.items():
            df.to_csv(output_path / f"Lake_{lake}.csv")





def process_rows(row, threshold):
    """
    Prüft eine Zeile auf Basis der angegebenen Grenzwerte.
    
    Args:
        row (Series): Eine Zeile des DataFrames.
        thresholds (dict): Grenzwerte für die Filterung.
    
    Returns:
        bool: True, wenn die Zeile gültig ist; False, wenn sie ausgeschlossen wird.
    """
    if row['nd_perc'] + row['cloud_perc'] + row['other_perc'] > threshold:
        return False
    else:
        return True

def filter_arlie_by_threshold(df, threshold):
        """
        Filtert den ARLIE-Datensatz basierend auf den angegebenen Grenzwerten.
        
        Args:
            dataframe (DataFrame): Der ursprüngliche DataFrame.
            thresholds (dict): Grenzwerte für die Filterung.
        
        Returns:
            DataFrame: Gefilterter DataFrame.
        """
        valid_rows= [
             row for _, row in df.iterrows() if
                process_rows(row, threshold) 
        ]

        return pd.DataFrame(valid_rows)


def aggregate_water_data(df, max_area_difference, id_column="river_km_id", target_id_column="Hylak_id"):
    issues = []

    # Datum extrahieren
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date

    # Prozent-Spalten erkennen
    perc_columns = [col for col in df.columns if col.endswith("_perc")]
    area_column = "area"

    # Hohe Wolkenbedeckungen etc. entfernen

    
    # Gewichtete Werte vorbereiten
    for col in perc_columns:
        df[f"{col}_weighted"] = df[col] * df[area_column]

    # Aggregation definieren
    aggregation_dict = {f"{col}_weighted": "sum" for col in perc_columns}
    aggregation_dict.update({
        "area": "sum",
        "gwp_id": "first",
        "object_nam": "first",
        "Lake_area_HyLak": "first",
        "Lake_name_HyLak": "first",
        "gwp_Area_max": "first",
        id_column: "first"
    })

    # Gruppieren
    df_grouped = df.groupby([target_id_column, "date"]).agg(aggregation_dict).reset_index()

    # Gewichtete Prozentwerte zurückrechnen
    for col in perc_columns:
        df_grouped[col] = df_grouped[f"{col}_weighted"] / df_grouped["area"]
        df_grouped.drop(columns=[f"{col}_weighted"], inplace=True)

    # Total-Check
    df_grouped["total_perc"] = df_grouped[perc_columns].sum(axis=1)

    # Problemfälle "total_perc ≠ 100" merken
    total_perc_issues = df_grouped.loc[df_grouped["total_perc"].round(1) != 100, target_id_column].unique()

    for lake_id in total_perc_issues:
        issues.append((lake_id, "total area not 100%"))
    
    # Fläche in km² umrechnen
    df_grouped['Arlie_Area'] = df_grouped['area'] * 1e-6  # Convert area to km²
    df_grouped['Gwp_Max_Area'] = df_grouped['gwp_Area_max']# * 1e-6  # Convert area to km²
    df_grouped = df_grouped.drop(columns=["total_perc", "area", "gwp_Area_max"])




    # Extent Difference Check
    arlie_area = df_grouped["Arlie_Area"].iloc[0]
    gwp_area = df_grouped["Gwp_Max_Area"].iloc[0]  # Achtung: wir nehmen einfach den ersten gwp_Area_max-Wert!

    deviation = abs(gwp_area - arlie_area) / gwp_area if gwp_area != 0 else 0

    if deviation >= max_area_difference:
        lake_id = df_grouped[target_id_column].iloc[0]
        issues.append((lake_id, f"Extent of lakes more than {max_area_difference}% different"))

    return df_grouped, issues

def make_arlie_files_to_dict(file_list, max_area_difference, max_disruption_threshold):
    arlie_dict = {}
    issues_list = []

    for file in file_list:
        #df = pd.read_csv(file, sep=",")
        print(f"Processing {file}...")
        try:
            df = pd.read_csv(file, sep=",")
         
        except pd.errors.ParserError as e:
            print(f"Error parsing {file}: {e}")
            continue  # Skip this file and continue with the next one
        # Schlüssel erstellen
   
        key = df['gwp_id'].iloc[0][:-14]  # Kürzen

        # Doppelte Zeitstempel löschen
        df = df.drop_duplicates(subset=['datetime'])
        df = filter_arlie_by_threshold(df, threshold = max_disruption_threshold)
        #print(df.columns)
        if df.empty:
            print(f"Warning: All rows in {file} were filtered out.")
            continue
        # Aggregieren
        agg_df, issues = aggregate_water_data(df, max_area_difference)

        # Ergebnisse sammeln
        arlie_dict[key] = agg_df
        issues_list.extend(issues)

    # Alle Probleme in DataFrame umwandeln
    issues_df = pd.DataFrame(issues_list, columns=["Hylak_id", "Comment"])

    return arlie_dict, issues_df


import re
def make_gwp_files_to_dict(root, arlie_dict, lat_lon_root):
    result_dict = {}

    # Prüfe, ob root ein String oder ein Path-Objekt ist
    if isinstance(root, str):
        root_path = Path(root)
    else:
        root_path = root

    # Liste alle Dateien im Verzeichnis auf
    files = [root_path / file for file in os.listdir(root_path) if os.path.isfile(root_path / file)]
    coord_files = [lat_lon_root / file for file in os.listdir(lat_lon_root) if os.path.isfile(lat_lon_root / file)]
    # Lade Koordinaten in ein Dictionary für schnellen Zugriff
    lat_lon_dict = {}
    for file in coord_files:
        file_stem = file.stem
        new_name = file_stem[:-14]  # Extrahiere den Basisnamen
        df_lat_lon = pd.read_csv(file, sep=";")
        lat_lon_dict[new_name] = (df_lat_lon['Lat'].iloc[0], df_lat_lon['Lon'].iloc[0])  # Nehme den ersten Eintrag
    

    for file in files:
        file_stem = file.stem  # Dateiname ohne Erweiterung
        
        # Extrahiere den Basis-Namen mit regex
        new_name = re.sub(r'(.*?)(_1_|_SGV-timeseries).*', r'\1', file_stem)
        #print(f"Verarbeite Datei: {file_stem}, extrahierter Name: {new_name}")

        # Suche nach passenden Einträgen im arlie_dict
        for gwp_id, arlie_df in arlie_dict.items():
            # Extrahiere die ID aus dem gwp_id (entferne "Lake" Präfix)
            
            #print(gwp_id)
            if new_name == gwp_id:
                #print(f"Treffer gefunden: {new_name} entspricht {gwp_id}")
                df = pd.read_csv(file, sep=";")

                arlie_df['date'] = pd.to_datetime(arlie_df['date']).dt.date
                df['Date'] = pd.to_datetime(df['Date']).dt.date
                first_date = arlie_df['date'].head(1).iloc[0]
                last_date = df['Date'].tail(1).iloc[0]
                #print(df.columns)
                merged_df = arlie_df.merge(
                    df, 
                    left_on='date',
                    right_on="Date",
                    how='left'
                )                
                merged_df = merged_df.drop(columns=['Date']).set_index('date')
                merged_df['GWP_Area'] = merged_df['Area']
                merged_df['GWP_water_perc'] = merged_df['GWP_Area'] * 100 / merged_df['Gwp_Max_Area']
                
                key_name = merged_df["Hylak_id"].iloc[0]  # Nimm den ersten Wert
                merged_df.drop(columns = ["Area", "object_nam"])
                
                
                # Füge die Koordinaten aus dem lat_lon_dict hinzu
            
                if gwp_id in lat_lon_dict:
                    lat, lon = lat_lon_dict[gwp_id]
                    merged_df['Latitude'] = lat
                    merged_df['Longitude'] = lon
                filtered_merged_df = merged_df[(merged_df.index >= first_date) & (merged_df.index <= last_date)]

                result_dict[f"Lake{key_name}"] = filtered_merged_df
    

    return result_dict


def create_gwp_based_dict(dict):
    gwp_arlie_dicts = {}

    for aoi, df in dict.items():
        for id, sub_df in df.groupby("Hylak_id"):
            new_key = f"Lake_{str(int(id))}"

            gwp_arlie_dicts[new_key] = sub_df.reset_index(drop=True)

    return gwp_arlie_dicts
    
def find_multiple_assignments(gwp_arlie_dicts):
    """
        Identifiziert ARLIE-Seen, die mehreren HydroLAKES zugeordnet sind.
        
        Args:
            lake_dict: Dictionary mit HydroLAKES-IDs als Schlüssel und DataFrames als Werte
            
        Returns:
            Dictionary mit ARLIE-IDs als Schlüssel und Mengen von zugeordneten HydroLAKES-IDs als Werte
    """
    
    arlie_to_hylak = {}
    multiple_assignments = {}
    for lake_key, df in gwp_arlie_dicts.items():
                
        unique_pairs = df[["river_km_id", "Hylak_id"]].drop_duplicates()

        for _, row in unique_pairs.iterrows():
            arlie_id = row['river_km_id']
            hylak_id = row['Hylak_id']

            if arlie_id in arlie_to_hylak:
                if hylak_id not in arlie_to_hylak[arlie_id]:
                    arlie_to_hylak[arlie_id].add(hylak_id)

            else:
                arlie_to_hylak[arlie_id] = {hylak_id}


    multiple_assignments = {arlie_id: hylak_ids for arlie_id, hylak_ids in arlie_to_hylak.items()
                            if len(hylak_ids) > 1}
        
    assignment_counts = {}

    for arlie_id, hylak_ids in multiple_assignments.items():
        count = len(hylak_ids)

        if count in assignment_counts:
            assignment_counts[count] += 1
        else:
            assignment_counts[count] = 1

    # Ausgabe der Ergebnisse
    print(f"Insgesamt {len(multiple_assignments)} von {len(arlie_to_hylak)} ARLIE-Seen sind mehrfach zugeordnet. Es gibt {len(gwp_arlie_dicts.keys())} GWP Samples")
    print("\nVerteilung der Mehrfachzuordnungen:")
    for count, num_rivers in sorted(assignment_counts.items()):
        print(f"  {num_rivers} Seen sind jeweils {count} verschiedenen HydroLAKES zugeordnet")

    # Beispiele für mehrfach zugeordnete Seen
    print("\nMehrfach zugeordnete Seen:")
    for arlie_id, hylak_ids in list(multiple_assignments.items()):  # Die ersten 5 Beispiele
        print(f"id {arlie_id} ist zugeordnet zu HydroLAKES: {hylak_ids}")
        
    return arlie_to_hylak, multiple_assignments

def drop_multiple_assigned_hylaks(multiple_assignments, gwp_arlie_dict):
    keys_to_remove = []

    for k, l in multiple_assignments.items():
        for i in l:
            keys_to_remove.append(f"Lake_{i}")
        
        # Neues Dictionary erstellen ohne die zu entfernenden Schlüssel
        filtered_dict = {k: v for k, v in gwp_arlie_dict.items() if k not in keys_to_remove}
        
    
        
    return filtered_dict

def find_min_max_length(input_dict, min_length_to_keep_df=50):
    """
    Analyzes a dictionary with DataFrames as values and returns statistics.
    
    Args:
        input_dict (dict): A dictionary with keys and DataFrames as values
        min_length_to_keep_df (int): Minimum number of rows to keep a DataFrame
    
    Returns:
        tuple: (min_length, max_length, cleaned_dict, length_df)
    """
    if not input_dict:
        print("Warning: Empty dictionary provided.")
        return 0, 0, {}, pd.DataFrame(columns=['key', 'length'])
    
    length_data = []
    keys_to_delete = []

    # Collect length information and identify which keys to delete
    for key, value in input_dict.items():
        if not isinstance(value, pd.DataFrame):
            print(f"Warning: Value for key '{key}' is not a DataFrame. Skipping.")
            keys_to_delete.append(key)
            continue
            
        # Drop rows with NaN in critical columns, if they exist
        if 'water_perc' in value.columns and 'GWP_water_perc' in value.columns:
            df = value.dropna(subset=['water_perc', 'GWP_water_perc'])
        else:
            df = value
            
        df_length = len(df)
        length_data.append({'key': key, 'length': df_length})
        
        if df_length < min_length_to_keep_df:
            print(f"Warning: {key} has fewer than {min_length_to_keep_df} rows ({df_length}). Will be removed.")
            keys_to_delete.append(key)

    # Create a copy of the dictionary and then delete keys
    cleaned_dict = {k: v for k, v in input_dict.items() if k not in keys_to_delete}

    # Calculate min/max with error handling for empty lists
    if cleaned_dict:
        valid_lengths = [entry['length'] for entry in length_data if entry['key'] in cleaned_dict]
        if valid_lengths:
            min_length = min(valid_lengths)
            max_length = max(valid_lengths)
        else:
            min_length = 0
            max_length = 0
    else:
        print("Warning: No DataFrames remained after filtering.")
        min_length = 0
        max_length = 0

    # Print summary statistics
    print(f"Found {len(cleaned_dict)} valid DataFrames after length filtering")
    if cleaned_dict:
        print(f"Valid DataFrame lengths range from {min_length} to {max_length}")
    
    # Return the results
    return min_length, max_length, cleaned_dict, pd.DataFrame(length_data)