# DLR-GWPIntercomparison
# Prerequesites
1. Download ARLIE Dataset for the whole time series (script 00_arlie_download_hda_files.py)
2. Extract Arlie zip files - script 00_extract_arlie_zipfiles.py

# Repository Structure
Each Processing step was assigend to a number:  

00 = Datadownload 
01 = Preprocessing  
02 = Matching GWP with a validation Dataset  
03 = calculate statistics  
04 = visualisation  


DLR-GWPIntercomparison/  
├── configs/  
│   ├── arlie.json  
│   ├── li.json  
│   ├── nasaflood.json  
│   ├── world_hydrolakes.json  
├── scripts/  
│   ├── 01_run_hydrolakes_processing.py  
│   ├──   
│   └── ...  
├── src/globallakevariability  
│   ├── preprocessing  
│   │   ├── add_maximum_extent.py  
│   │   ├── HydrolakesDataloader.py    
│   │   ├── ...  
│   └── utils  
│   │   ├── filehandling.py  
│   │   ├── ...  
├── notebooks/  
│   ├── exploration.ipynb  
│   └── validation.ipynb  
├── pyproject.toml  
└── README.md  

# Workflow

## Preprocessing
The Preprocessing matches the Global Waterpack files with a corresponding Hydrolake-id. It also appends the maximum extent of each lake to the output dataset. 

### 01_run_hydrolakes_processing
this script needs to be run twice: once for the ARLIE dataset and once for the whole wold. Use the world_hydrolakes.json for it.

uv run .\scripts\01_run_hydrolakes_processing.py --config .\configs\arlie.json


Input:
Output:
## Matching Global Waterpack with validation Datasets
### ARLIE: 02_run_arlie_gwp_matching.py

with this script all Arlie geometries are spatially joined with Hydrolakes geometries created in the Script 01_run_hydrolakes. Then the Arlie timeseries information are matched.

 uv run .\scripts\02_run_arlie_gwp_matching.py --config .\configs\arlie.json


Input: 
gwp_hydrolakes_max_extent
path to unzipped arlie files

Output: 
csv files for each gwp sample with in arlie aoi. 
containing the arlie timeseries + max extent information + gwp id 