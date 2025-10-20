from pathlib import Path
import geopandas as gpd
import pandas as pd
import os
from globallakevariability.utils.filehandling import get_filepaths_from_folder


def derive_max_extent_info(path_to_gwp_timeseries_folder: str):
    """
    Derives the maximum extent information from the GWP timeseries files and returns it as a DataFrame.
    """
    
    # Get all file paths from the GWP timeseries folder

    all_filepaths = get_filepaths_from_folder(Path(path_to_gwp_timeseries_folder))
    max_extent_df = pd.DataFrame()
    filename_list = []
    add_max_extent_info = []
    coordinate_id_list = []
    for file in all_filepaths:

        filename = os.path.basename(file)
        coordinate_id = filename.replace("_SGV-timeseries_allDates_rm2902.txt", "_coordinates")  # Remove file extension
        filename_list.append(filename)
        coordinate_id_list.append(coordinate_id)
        ts_file = pd.read_csv(file, sep = ";")
        max_extent = ts_file['Area'].max()
        add_max_extent_info.append(max_extent)

    max_extent_df['Filename'] = filename_list
    max_extent_df['gwp_Area_max'] = add_max_extent_info
    max_extent_df['Coordinate_ID'] = coordinate_id_list

    return max_extent_df



def add_max_extent_to_gwp(gwp_with_hylak_id: gpd.GeoDataFrame, max_extent_df: pd.DataFrame):
    """
    This function merges the maximum extent information to the gwp_with_hylak_id GeoDataFrame.
    
    Parameters:
    gwp_with_hylak_id (gpd.GeoDataFrame): GeoDataFrame containing GWP samples with matching Hydrolake IDs.
    max_extent_df (pd.DataFrame): DataFrame containing maximum extent information for each GWP lake.
    
    Returns:
    gpd.GeoDataFrame: Updated GeoDataFrame with maximum extent information added.
    """

    gwp_with_hylak_id = gpd.read_file(r"T:\DLR\Analysis3\Output\Hydrolakes\gwp_withHylaksAndMaxExtent_arlie.gpkg")
    ids = max_extent_df['Coordinate_ID'].tolist()    # Merge the max extent information to the gwp_with_hylak_id GeoDataFrame
    gwp_with_max_extent = gwp_with_hylak_id.merge(max_extent_df, left_on='id', right_on='Coordinate_ID', how='left')
    filtered_gwp_hylak_max_extent = gwp_with_max_extent[gwp_with_max_extent['id'].isin(ids)]
    
    filtered_gwp_hylak_max_extent = filtered_gwp_hylak_max_extent.drop(columns=['Coordinate_ID'])
    return filtered_gwp_hylak_max_extent
