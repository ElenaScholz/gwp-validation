from pathlib import Path
import os
def save_dict(data_dict, output_path):

    output_path = Path(output_path)

    os.makedirs(output_path, exist_ok=True)

    for lake, df in data_dict.items():
        gwp_id_coord = df['gwp_id'].iloc[0]
        gwp_id = gwp_id_coord[:-14]
        
        print(gwp_id)
        df.to_csv(output_path / f"{gwp_id}.csv")


import os
from zipfile import ZipFile
from pathlib import Path
import shutil

def extract_csv_files(zip_folder, output_folder):
    zip_folder = Path(zip_folder)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    file_counters = {}

    for zip_path in zip_folder.glob("*.zip"):
        with ZipFile(zip_path, 'r') as zip_ref:
            for file_name in zip_ref.namelist():
                if file_name.lower().endswith('.csv'):
                    zip_ref.extract(file_name, output_folder)
                    base_name = Path(file_name).stem
                    ext = Path(file_name).suffix
                    # Increment counter for each base_name
                    count = file_counters.get(base_name, 0) + 1
                    file_counters[base_name] = count
                    # Format counter as 3 digits with leading zeros (e.g., 001, 002)
                    new_name = f"{count:03d}_{base_name}{ext}"
                    src = output_folder / file_name
                    dst = output_folder / new_name
                    shutil.move(str(src), str(dst))
