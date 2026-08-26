import argparse
import subprocess
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--config", type=str, required=True, help="Path to the JSON configuration file")
args = parser.parse_args()
CONFIG_PATH = args.config

# Load config to get output file path
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

input_root = Path(config["root_dir"])
output_dir = input_root / config["matching"]["output_directory"]

# Check for any CSV files in the output directory
csv_files = list(output_dir.glob("*.csv"))

if not csv_files:
    print(f"Running 02.1_run_arlie_gwp_geom_matching.py because no CSV files found in {output_dir}.")
    subprocess.run(
        [sys.executable, "scripts/arlie/02.1_run_arlie_gwp_geom_matching.py", "--config", CONFIG_PATH],
        check=True
    )
else:
    print(f"Skipping 02.1_run_arlie_gwp_geom_matching.py because CSV files already exist in {output_dir}.")

# Step 2: Always run 02.2
processed_data_dir = input_root / config["matching"]["processed_data_directory"]
# Check for any CSV files in the output directory
csv_files_validation = list(processed_data_dir.glob("*.csv"))

if not csv_files_validation:
    print(f"Running 02.2_run_arlie_gwp_ts_matching.py because no CSV files found in {processed_data_dir}.")
    subprocess.run(
        [sys.executable, "scripts/arlie/02.2_run_arlie_gwp_ts_matching.py", "--config", CONFIG_PATH],
        check=True
    )
else:
    print(f"Skipping 02.2_run_arlie_gwp_ts_matching.py because CSV files already exist in {processed_data_dir}.")
