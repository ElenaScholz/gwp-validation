from pathlib import Path
import geopandas as gpd
import pandas as pd
import os
import json
import argparse
from globallakevariability.preprocessing.GlakesProcessor import GLAKESProcessor
from globallakevariability.preprocessing.postprocessingGlakes import merge_hylak_glakes_strict

def main(config):
    gwp_lakes = config
    continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="match GWP lakes with GLAKES and HydroLAKES datasets")
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
