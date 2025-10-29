# DLR-GWPIntercomparison
# Get started
1. Go to github and fork this repository. 
2. Clone your fork to a directory of your choice:: `git clone <the github url to your fork>´

This project is setup as a Python Package. Therefore the scripts can be run with commands like this: 

`uv python run ... `

## Environment setup
This project uses two virtual environments: one managed via uv and one via pixi.

uv environment: Used for nearly all scripts.

pixi environment: Used only for the script that processes NASA Flood Product data, as it contains gdal.

### uv Environment
1. If you don't have uv installed yet, follow the official guide: [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

2. To set up the environment, run: `uv sync` in your terminal.  

### pixi
1. If you don't habe pixi installed yet, follow the official guide: [pixi installation guide](https://pixi.sh/dev/installation/)  

2. To set up the envirnment, run `pixi sync` in your terminal.  
# Repository Structure
Each Processing step was assigend to a number:  

00 = Datadownload   
01 = Preprocessing  
02 = Matching GWP with a validation Dataset/Hydrolakes  
03 = calculate statistics  
04 = visualisation  


DLR-GWPIntercomparison/  
├── configs/  
│   ├── arlie.json  
│   ├── li.json  
│   ├── nasaflood.json  
│   ├── world_hydrolakes.json  
│   ├── europe_hydrolakes.json  
│   ├── stats.json  
├── notebooks/  
│   ├── getInfoForPaper.ipynb  
│   └── plots.ipynb  
├── scripts/  
│   ├── arlie  
│   │   ├── 00_arlie_download_hda_files.py    
│   │   ├── 00_extract_arlie_zipfiles.py  
│   │   ├── 02.1_run_arlie_gwp_geom_matching.py  
│   │   ├── 02.2_run_arlie_gwp_ts_matching.py  
│   ├── Li  
│   │   ├── 01.1_matchGlakesHydrolakesGWP.py  
│   │   ├── 01.2_reshapeMonthly_LiLSE.py  
│   │   ├── 01.3_reshape_monthlyGWP.py   
│   ├── NasaFloodProduct  
│   │   ├── 00_Download_GWP_raster.py        
│   │   ├── 01.1_clip_GWP_to_tiles.py  
│   │   ├── 01.2_NasaFlood_extractHDF.py      
│   │   ├── 01.3_run_GWPNasaFlood_calculate_zonal_statistics.py    
│   ├── 02_run_hydrolakes_processing.py   
│   └── 02_run_match_arlie_complete.py    
│   └── 02_run_match_GWP_NasaFloodProduct.py  
│   └── 02.1_run_matchGWPandLiByGlakes.py  
│   └── 02.2_run_LiProcessData.py  
│   └── 03_statistics.py  
│   └── 04_visualisations.py
├── src/globallakevariability  
│   ├── matching
│   │   ├── arlieProcessor.py  
│   ├── preprocessing  
│   │   ├── add_maximum_extent.py  
│   │   ├── filehandling.py  
│   │   ├── HydrolakesDataloader.py    
│   │   ├── GlakesProcessor.py  
│   │   ├── postprocessingGlakes.py  
│   │   ├── zonal_statistics.py  
│   ├── stats  
│   │   ├── statistics.py  
│   ├── utils  
│   │   ├── helper.py
│   ├── vis  
│   │   ├── visualisation.py    
├── pyproject.toml
├── uv.lock    
├── pixi.toml  
├── pixi.lock  
└── README.md  

# Workflow
## Data download 
### Hydrolakes
Download the Hydrolakes dataset in Shapefile-Format from this website: [Hydrolakes:](https://www.hydrosheds.org/products/hydrolakes#downloads). 

### Aggregated River and Lake Ice Extent (ARLIE)
1. Download the ARLIE dataset for the whole time series (2003-2024). You can use the Script: 00_arlie_download_hda_files.py

We used the maximum spatial extent for the dataset. [Information about it can be found here](https://www.eea.europa.eu/en/datahub/datahubitem-view/b5c68a06-5dcf-42e5-baad-94f861189f91). 

Note that the Area of interest needs to be geopackage file and that you need login credential for the hda-file donwload. 
2. Afterwards the files need to be unzipped. To do so use the script: 00_extract_arlie_zipfiles.py

### Global Water Pack Raster (GWP)
Global Water Pack comes as global raster datasets. Those can be downloaded with the script `00_Download_GWP_raster.py`.

Note: We used already processed time series containing daily Lake Area information in km² for the whole timeseries, as well as coordinates for each lake in form of latitude/longitude information.
Each lake is stored in a seperate csv file. 

Furthermore we removed the 29.02. for all leap years.

### Nasa Flood Product

pixi run python .\scripts\NasaFloodProduct\00_NasaFlood_extract_HDF.py --config .\configs\nasaflood.json)


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

### Nasa Flood Product: Calculate Zonal statistics and match time series

Firstly run the script 01.1_run_GWPNasaFlood_calculate_zonalStatistics.py with the following command. 

uv run python .\scripts\01.1_run_GWPNasaFlood_calculate_zonalStatistics.py --config .\configs\nasaflood.json

After this process is finished use the Script 02_run_match_GWP_NasaFloodProduct.py. 

### Monthly Lake Surface Area by Li et al.

Run the Scripts 02.1_run_matchGWPandLiByGlakes.py as well as 02.2_run_LiProcessData.py.

## Statistics

## Visualisations