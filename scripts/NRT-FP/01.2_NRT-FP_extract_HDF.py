# this script uses the pixigeo environment! 
# It extracts single GeoTiffs from the MCDWD Flood Product hdf files

from osgeo import gdal
from pathlib import Path
import os
import json
import argparse


def main(config):
    gdal.UseExceptions()
    ROOT = Path(config["root_dir"])
    # Change Paths to directories
    INPUT_DIR = ROOT / config["preprocessing"]["MWP_WorldMap_Dir"]
    FOLDER = os.listdir(INPUT_DIR)
    FOLDER_PATHS = [INPUT_DIR / folder for folder in FOLDER]
    OUTPUT_PATH = ROOT / config["preprocessing"]["output_dir_nasaflood"]
    print(FOLDER_PATHS)

    for folder_path in FOLDER_PATHS:
        # Check if it's really a directory
        if folder_path.is_dir():
            # Get the folder name for output structure
            folder_name = folder_path.name
            print(f"Processing folder: {folder_name}")
            
            # Create output folder for this tile if it doesn't exist
            output_folder = OUTPUT_PATH / folder_name
            if not output_folder.exists():
                output_folder.mkdir(parents=True, exist_ok=True)
            
            print(f"Output folder: {output_folder}")
            # Iterate over all files in the subfolder
            for hdf_path in folder_path.iterdir():
                if hdf_path.is_file():  # Ensure it's a file
                    subdataset = f'HDF4_EOS:EOS_GRID:"{hdf_path}":Grid_Water_Composite:Flood_3Day_250m'
                    
                    #filename = str(hdf_path)[39:67] + ".tif"
                    filename = hdf_path.stem + ".tif"  
                    # check if the output folder exists, if not create it
                    output_folder.mkdir(parents=True, exist_ok=True)
                    
                    output_file = output_folder / filename
                    
                    try:
                        ds = gdal.Open(subdataset)
                        if ds is None:
                            raise RuntimeError(f"Could not open dataset: {subdataset}")

                        # Export as GeoTIFF with compression and tile option
                        gdal.Translate(str(output_file), ds, creationOptions=['COMPRESS=DEFLATE', 'TILED=YES'])
                        print(f"Export successful: {output_file}")

                        # Clean up
                        ds = None

                    except Exception as e:
                        print(f"Error processing {hdf_path}: {e}")

    print("Conversion completed!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Hydrolakes and GWP data based on configuration file.")
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