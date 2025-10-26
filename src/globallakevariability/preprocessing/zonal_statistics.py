import rasterio as rio
import rasterstats
import pandas as pd
import geopandas as gpd
import numpy as np 
import os
from pathlib import Path
from globallakevariability.preprocessing.filehandling import get_filepaths_from_folder 
import argparse
import re
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging
from tqdm import tqdm

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zonal_stats_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def concat_gwp_and_mwp(gwp_df, mwp_df):
    gwp_water_info = gwp_df[["gwp-Water", "gwp-noWater", "gwp-count"]]

    result = pd.concat([mwp_df, gwp_water_info], axis=1)

    return result

def calculate_zonal_statistics(input_raster_path, max_extent, categories, count_name, year, doy, statistical_value_list = ["count"]):

    # open the files
    lakes = max_extent
    rf = rio.open(input_raster_path, mode="r")
    try: 
        lakes.geometry = lakes.geometry.make_valid()
        if lakes.crs != rf.crs:
            lakes = lakes.to_crs(rf.crs)
        # create numpy array and get affine infos
        rf_array = rf.read(1)
        affine = rf.transform
        nodata = rf.nodata

        # Handle nodata based on raster data type
        if rf_array.dtype == np.uint8:
            if nodata == 255.0:
                nodata = 6  # Use dummy value so 255 is counted as valid data
            elif nodata is None or nodata < 0 or nodata > 255:
                nodata = 6  # Use dummy value for uint8, all actual values will be counted


        if nodata is not None:
            valid_pixels = np.sum(rf_array != nodata)
        else:
            valid_pixels = np.sum(~np.isnan(rf_array))

        if valid_pixels == 0:
            print(f"No valid data in {input_raster_path}")
            return pd.DataFrame()

        # calcualte zonal statistics
        zonal_stats = rasterstats.zonal_stats(lakes, rf_array,
                                            #nodata = -999, 
                                            nodata = nodata,
                                            affine = affine, 
                                            categorical = True,
                                            stats = statistical_value_list,
                                            category_map = categories, 
                                            geojson_out = True
                                            )

        # make a pandas dataframe as result:
        i = 0
        stats_list = []
        while i < len(zonal_stats):
            stats_list.append(zonal_stats[i]['properties'])
            i = i+1

        zonal_stats_df = pd.DataFrame(stats_list)
        zonal_stats_df = zonal_stats_df.rename(columns={"count" :count_name})

        if year is not None and doy is not None:
            zonal_stats_df['year'] = year
            zonal_stats_df['doy'] = doy

    except Exception as e:
        logger.error(f"Error in calculate_zonal_stats_df for {input_raster_path}: {str(e)}")
        raise
        #print(f"Error in calculate_zonal_stats_df for {input_raster_path}: {str(e)}")

    return zonal_stats_df

def find_matching_files(gwp_path, mwp_path, year, tile, max_files=None):

    """
    Find matching GWP and MWP files based on date.
    New naming conventions:
    - GWP: "GWP.OSWF.DAILY.20100101.v1_MCDWD.h06v04.2010.tif"
    - MWP: "MCDWD_L3.A2010001.h06v04.061.tif"
    
    Returns a list of tuples (gwp_file_path, mwp_file_path, date_obj, doy)
    """
    try:
        # Pfade zu Dateien abrufen
        gwp_files = get_filepaths_from_folder(gwp_path)
        mwp_files = get_filepaths_from_folder(mwp_path)
        
        # Erstelle ein Dictionary mit MWP-Dateinamen für schnellere Suche
        # Key: (year, doy, tile) -> Value: file_path
        mwp_dict = {}
        for path in mwp_files:
            filename = path.name
            # Parse MWP filename: MCDWD_L3.A2010001.h06v04.061.tif
            mwp_match = re.search(r"MCDWD_L3\.A(\d{4})(\d{3})\.([hv\d]+)\.", filename)
            if mwp_match:
                mwp_year = mwp_match.group(1)
                mwp_doy = mwp_match.group(2)
                mwp_tile = mwp_match.group(3)
                key = (mwp_year, mwp_doy, mwp_tile)
                mwp_dict[key] = path
        
        matched_files = []
        
        for gwp_file_path in gwp_files:
            if max_files is not None and len(matched_files) >= max_files:
                break
                
            gwp_filename = gwp_file_path.name
            
            # Parse GWP filename: GWP.OSWF.DAILY.20100101.v1_MCDWD.h06v04.2010.tif
            gwp_match = re.search(r"GWP\.OSWF\.DAILY\.(\d{8})\.([hv\d]+)", gwp_filename)
            
            if not gwp_match:
                logger.warning(f"Kein gültiges GWP-Format gefunden in: {gwp_filename}")
                continue
                

            if gwp_match:
                date_str = gwp_match.group(1)  # "20100101"
                gwp_tile = gwp_match.group(2)  # "h06v04"
                #print(f"Date: {date_str}, Tile: {gwp_tile}")
                    
            # Filter by tile if specified
            if tile and gwp_tile != tile:
                continue
                
            try:
                date_obj = datetime.strptime(date_str, "%Y%m%d")
                doy = date_obj.timetuple().tm_yday
                doy_str = f"{doy:03d}"
                file_year = date_obj.year
                
                # Filter by year if specified
                if year and file_year != int(year):
                    continue
                
                # Look for matching MWP file
                search_key = (str(file_year), doy_str, gwp_tile)
                
                if search_key in mwp_dict:
                    mwp_file_path = mwp_dict[search_key]
                    matched_files.append((gwp_file_path, mwp_file_path, date_obj, doy))
                    logger.debug(f"Match gefunden: {gwp_filename} <-> {mwp_file_path.name}")
                else:
                    logger.debug(f"Keine entsprechende MWP-Datei gefunden für: {gwp_filename} (Suche nach Jahr={file_year}, DOY={doy_str}, Tile={gwp_tile})")
                    
            except ValueError as e:
                logger.warning(f"Fehler beim Parsen des Datums in {gwp_filename}: {e}")
                continue
        
        logger.info(f"Insgesamt {len(matched_files)} passende Dateipaare gefunden")
        
        
        return matched_files
    
        
    except Exception as e:
        logger.error(f"Fehler beim Suchen von Dateien für {tile}, {year}: {str(e)}")
        return []
    


def process_in_batches(file_pairs, max_extent, year, tile, chunk_size, num_workers ):
    """
    Process file pairs in batches to control memory usage.
    """
    all_results = []

    # Split the file pairs into chunks
    for i in range(0, len(file_pairs), chunk_size):
        chunk = file_pairs[i:i + chunk_size]
        batch_args = [(gwp, mwp, max_extent, year, doy, tile) for gwp, mwp, _, doy in chunk]
        
        # Process the current batch using multiple workers
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            # unpack each tuple so process_file_pair gets individual args
            futures = [executor.submit(process_file_pair, *arg) for arg in batch_args]
            
            # Collect results as they complete
            for future in tqdm(as_completed(futures), total=len(futures), desc=f"Processing batch {i//chunk_size + 1}/{(len(file_pairs) + chunk_size - 1) // chunk_size}"):
                result = future.result()
                if result is not None:
                    all_results.append(result)
    
    # Combine all batch results
    if all_results:
        return pd.concat(all_results, ignore_index=True)
    else:
        return pd.DataFrame()
    

def process_file_pair(gwp_file, mwp_file, max_extent, year, doy, tile):


    try:
        logger.debug(f"Verarbeite Dateien: {gwp_file.name} und {mwp_file.name}")
        
        gwp_stats_df = calculate_zonal_statistics(gwp_file, max_extent, count_name="gwp-count", year = year, doy = doy,
                                                      categories = {0.0 : "gwp-noWater", 1.0 : "gwp-Water"} ,
                                                      statistical_value_list=['count'])
        mwp_stats_df = calculate_zonal_statistics(mwp_file, max_extent, count_name="mwp-count", year = year, doy = doy,
                                                     categories = {0.0 : "mwp-noWater", 
                                                               1.0 : "mwp-surfaceWater", 
                                                               2.0: "mwp-recurringFlood", 
                                                               3.0: "mwp-Flood", 
                                                               255.0 : "mwp-insufficientData"},
                                                     statistical_value_list=['count'])
        
        combined_df = concat_gwp_and_mwp(gwp_stats_df, mwp_stats_df)

        combined_df['tile'] = tile
        combined_df['year'] = year
        combined_df['doy'] = doy
        combined_df['date'] = datetime(year, 1, 1) + pd.Timedelta(days=doy-1)
        
        return combined_df
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung von {gwp_file.name} und {mwp_file.name}: {str(e)}")
        return None

def process_tile_year(tile, year, gwp_path, mwp_basepath, max_extent_path, chunk_size, num_workers, max_files_per_tile_year):
    """
    Process all file pairs for a specific tile and year combination.
    """
    try:
        logger.info(f"Verarbeite Tile {tile} für Jahr {year}")
        # Pfade zu den Ordnern

        gwp_path = gwp_path / tile
        mwp_path = mwp_basepath / f"MCDWD.{tile}.{year}"
        # Lade max_extent nur einmal
        max_extent_file = max_extent_path / f"{tile}_extent.gpkg"
        if not max_extent_file.exists():
            logger.error(f"Max extent file nicht gefunden: {max_extent_file}")
            return pd.DataFrame()
            
        max_extent = gpd.read_file(max_extent_file)
        print(print(f"Features: {len(max_extent)}, CRS: {max_extent.crs}"))
        # Finde passende Dateien
        matched_files = find_matching_files(gwp_path, mwp_path, year, tile, max_files_per_tile_year)
        
        if not matched_files:
            logger.warning(f"Keine passenden Dateien für {tile}, {year} gefunden")
            return pd.DataFrame()
            
        logger.info(f"{len(matched_files)} passende Dateien für {tile}, {year} gefunden")
        
        # Verarbeite die Dateien in Batches
        result_df = process_in_batches(
            matched_files, 
            max_extent, 
            year, 
            tile, 
            chunk_size,
            num_workers
        )
        
        return result_df
    
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung von {tile}, {year}: {str(e)}")
        return pd.DataFrame()
    
def apply_area_deviation_check(df, max_area_difference=0.1):
        """
        Überprüft die Pixel-Konsistenz zwischen GWP und MWP Daten
        
        Parameters:
        -----------
        df : DataFrame
            See-Daten mit gwp-count und mwp-count Spalten
        max_area_difference : float, default=0.1
            Maximale erlaubte relative Abweichung (0.1 = 10%)
        
        Returns:
        --------
        clean_df : DataFrame
            Datenpunkte die den Konsistenz-Check bestehen
        removed_df : DataFrame
            Datenpunkte die den Check nicht bestehen
        """
        
        # Pixel-Konsistenz Check
        df['pixel_deviation'] = np.where(
            df['gwp-count'] != 0,
            abs(df['gwp-count'] - df['mwp-count']) / df['gwp-count'],
            0
        )
        
        # Filter anwenden
        consistency_mask = df['pixel_deviation'] <= max_area_difference
        
        clean_df = df[consistency_mask].copy()
        removed_df = df[~consistency_mask].copy()
        
        return clean_df, removed_df