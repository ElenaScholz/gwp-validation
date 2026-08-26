import os
from zipfile import ZipFile
from pathlib import Path
import shutil
from globallakevariability.utils.helper import extract_csv_files

if __name__ == "__main__":
    zip_folder = r"Path/To/You/Inputfolder/ARLIE/zip"
    output_folder = r"Path/To/You/Inputfolder/ARLIE/files"
    extract_csv_files(zip_folder, output_folder)