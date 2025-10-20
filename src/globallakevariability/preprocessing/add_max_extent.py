from pathlib import Path
import geopandas as gpd
import pandas as pd
import os
#from globallakevariability.utils.filehandling import get_filepaths_from_folder

def get_filepaths_from_folder(folderPath):
    '''Extracts all filepathes from a folder'''
    all_pathes = []
    filenames = os.listdir(folderPath)
    for name in filenames:
        path = folderPath / name
        all_pathes.append(path)
    return all_pathes

gwp_with_hylak_id = gpd.read_file(r"T:\DLR\Analysis3\Output\Hydrolakes\gwp_withHylaksAndMaxExtent_arlie.gpkg")
path_to_gwp_timeseries_folder = r"T:\DLR\Analysis3\Input\GWP\05_timeseries_8247_rm2902"

def derive_max_extent_info(path_to_gwp_timeseries_folder: str):
    """
    This function adds the maximum extent information to the gwp_with_hylak_id GeoDataFrame.
    
    Parameters:
    gwp_with_hylak_id (gpd.GeoDataFrame): GeoDataFrame containing GWP samples with matching Hydrolake IDs. Please Note: this file is generated with the hydrolakes_dataloader class.
    path_to_gwp_timeseries_folder (str): Path to the folder containing vector files with the maximum extent of the GWP lakes.
    
    Returns:
    tuple:
    - gwp_with_hylakID (GeoDataFrame): per-sample dataset with max area
    - gdf_with_area_sum (GeoDataFrame): per-sample with aggregated area merged
    - df_area_sum (DataFrame): aggregated area per GWP/Hylak pair

    Note: The outputs will contain duplicated Hydrolakes Ids as one lake can be covered by multiple modis tiles. 
    The lakesize information as well as the time series themselves are already aggregated to one lake per id - but for matching purposes the duplicated ids are kept.
    They will be removed in the next steps of the analysis.
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
    max_extent_df['Max_Extent'] = add_max_extent_info
    max_extent_df['Coordinate_ID'] = coordinate_id_list

    return max_extent_df


max_extent_df = derive_max_extent_info(path_to_gwp_timeseries_folder)
print(max_extent_df)

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
    gwp_with_max_extent = gwp_with_hylak_id.merge(max_extent_df, left_on='id', right_on='Filename', how='left')
    filtered_gwp_hylak_max_extent = gwp_with_max_extent[gwp_with_max_extent['id'].isin(ids)]
    
    
    return filtered_gwp_hylak_max_extent

gwp_with_max_extent = add_max_extent_to_gwp(gwp_with_hylak_id, max_extent_df)
print(gwp_with_max_extent.head())
print(gwp_with_max_extent.columns)