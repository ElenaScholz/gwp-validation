# DLR-GWPIntercomparison
# Environment setup
For this projects two virtual environments are used: One managed via uv and the other one via pixi. 

You will use the uv environment vor nearly all scripts. There is one Script that processes Data of the NASA Flood Product that uses the pixi environment as it contains gdal. It is indicated in the script 
## uv

## pixi


# Prerequesites
1. Download ARLIE Dataset for the whole time series (script 00_arlie_download_hda_files.py)
2. Extract Arlie zip files - script 00_extract_arlie_zipfiles.py
3. Download the GWP Raster datasets: use the script 00_Download_GWP_raster.py
4. Convert Nasa Flood Product files from HDF to GeoTIFFS (windows Power Shell:   
pixi run python .\scripts\NasaFloodProduct\00_NasaFlood_extract_HDF.py --config .\configs\nasaflood.json)

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
│   ├── arlie
│   │   ├──  
│   │   ├──    
│   ├── NasaFloodProduct
│   │   ├── 00_NasaFlood_extractHDF.py    
│   │   ├──  
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
- hydrolakes Shapefile
- gwp coordinate files
- gwp timeseries files
Output:
- gpkg/csv file where each point of gwp also contains information of hydrolakes id as well as the laximum area extent.
  
## Matching Global Waterpack with validation Datasets
### ARLIE: 02_run_match_arlie_complete.py

uv run .\scripts\02_run_match_arlie_complete.py --config .\configs\arlie.json

This script contains two subscripts saved in the arlie folder:
1. 02.1_run_arlie_gwp_geom_matching.py
2. 02.2_run_arlie_gwp_ts_matching.py

The first script joins all Arlie geometries spatially with Hydrolakes geometries created in the Script 01_run_hydrolakes. 

Then the Arlie timeseries information are matched.

 uv run .\scripts\arlie\02_run_arlie_gwp_matching.py --config .\configs\arlie.json

In the second script the gwp timeseries information are matched. The following checks are made:
- Checking for Lake Area differences of more then 10%
- Filtering out all dates where ARLIE has a disruption (Cloud Coverage + Other entities + XX) higher then 10%
- then checking if there is a minimum length of 50 entries for each file. Removing all files with less entries. 


Input: 
gwp_hydrolakes_max_extent
path to unzipped arlie files

Output: 
csv files for each gwp sample with in arlie aoi. 
containing the arlie timeseries + max extent information + gwp id 

### Nasa Flood Product: 02_run_match_GWP_NasaFloodProduct.py

