import os 
from pathlib import Path

def get_output_filename(output_dir, aoi):
    """Generate output filename based on AOI."""
    return Path(output_dir) / f"gwp_withHylaksAndMaxExtent_{aoi}.gpkg"


def get_csv_filename(gpkg_path, suffix):
    """Generate CSV filename from GPKG path."""
    return str(gpkg_path).replace(".gpkg", f"_{suffix}.csv")


def get_gpkg_filename(gpkg_path, suffix):
    """Generate GPKG filename from base GPKG path."""
    return str(gpkg_path).replace(".gpkg", f"_{suffix}.gpkg")

def get_filepaths_from_folder(folderPath):
    '''Extracts all filepathes from a folder'''
    all_pathes = []
    filenames = os.listdir(folderPath)
    for name in filenames:
        path = folderPath / name
        all_pathes.append(path)
    return all_pathes