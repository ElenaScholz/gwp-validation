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
