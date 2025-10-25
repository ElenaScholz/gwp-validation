from pathlib import Path
import os
import pandas as pd
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