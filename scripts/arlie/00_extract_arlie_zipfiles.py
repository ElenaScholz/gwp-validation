import os
from zipfile import ZipFile
from pathlib import Path
import shutil
from globallakevariability.utils.helper import extract_csv_files

if __name__ == "__main__":
    zip_folder = r"T:/GlobalWaterPack_Product_Intercomparison/INPUT/ARLIE/zip"
    output_folder = r"T:/GlobalWaterPack_Product_Intercomparison/INPUT/ARLIE/files"
    extract_csv_files(zip_folder, output_folder)