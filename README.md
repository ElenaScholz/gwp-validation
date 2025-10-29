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
│   ├── 01_run_hydrolakes_processing.py   
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


# Folder Structure for Data processing
Main Data Folder/  
├── Input/  
│   ├── ARLIE  
│   │   ├── zip
│   │   ├── files
│   │   │   ├── 001_arlie.csv  
│   │   │   ├── 001_geometries.csv  
│   │   │   └── 00x_... .csv    
│   │   └── arlie_bbox.gpkg
│   ├── GWP  
│   │   ├── 00_coordinates_8247
│   │   ├── *Folders for preprocessed gwp timeseries*
│   │   ├── 05_timeseries_8247_rm2902
│   │   ├── 06_timeseries_8247_rm2902_monthly  
│   │   └── 06_timeseries_8247_rm2902_monthly_hylakIDs  
│   ├── HydroLAKES_polys_v10  
│   ├── Li
│   │   ├── GLAKES
│   │   ├── Glakes_Prepared
│   │   ├── Monthly_Lakes
│   │   └── monthly_lake_surface_extent.csv  
│   ├── NASAFlood  
│   │   ├── 01_GlobalGWP  
│   │   ├── 01_MWP  
│   │   ├── 02_GWP-tiles  
│   │   ├── 02_MWP_gtiff  
│   │   └── max_extent_tiles  
├── Output
│   ├── allValidationDatasets  
│   ├── ARLIE  
│   ├── GWP  
│   ├── Hydrolakes  
│   ├── Li
│   ├── NASAFlood  
├── Results
├── Maps
└── Plots


# Workflow
## Data download 
### Hydrolakes
Download the Hydrolakes dataset in Shapefile-Format from this website: [Hydrolakes:](https://www.hydrosheds.org/products/hydrolakes#downloads). 

### Aggregated River and Lake Ice Extent (ARLIE)
1. Download the ARLIE dataset for the whole time series (2003-2024). You can use the Script: *00_arlie_download_hda_files.py*

We used the maximum spatial extent for the dataset. [Information about it can be found here](https://www.eea.europa.eu/en/datahub/datahubitem-view/b5c68a06-5dcf-42e5-baad-94f861189f91). 

Note that the Area of interest needs to be **geopackage file** and that you need login credential for the hda-file donwload. 

Please download geometries as well as timeseries files. 

2. Afterwards the files need to be unzipped. To do so use the script: *00_extract_arlie_zipfiles.py* 

### Global Water Pack Raster (GWP)
Global Water Pack comes as global raster datasets. Those can be downloaded with the script `00_Download_GWP_raster.py`.

**Note:** We used already processed time series dataset containing daily Lake Area information in km², as well as coordinates for each lake in form of latitude/longitude information.
The information are stored in two corresponding files: one containing coordinates, one the time series.  

Furthermore we removed the 29.02. for all leap years.

### Near realtime Flood Product (Nasa Flood Product)

The [near realtime global Flood Product](https://www.earthdata.nasa.gov/data/instruments/viirs/near-real-time-data/nrt-global-flood-products) provided by NASA is online available for recent years. We used historical data provided by NASA for the years 2010 and 2021. 

The NASA Flood Product comes in hdf-fileformat. To extract the datasets use the script *00_NasaFlood_extract_HDF.py* in the terminal: 

`pixi run python .\scripts\NasaFloodProduct\00_NasaFlood_extract_HDF.py --config .\configs\nasaflood.json`

### Global Lake Surface Extent dataset 
The Global Lake Surface Extent dataset was published in mid 2025 within the paper [Global dominance of seasonality in shaping lake-surface-extent dynamics](https://www.nature.com/articles/s41586-025-09046-3#data-availability) by Li et al. 

Data is available [here:](https://zenodo.org/records/15536395)
We used the *monthly_lake_surface_extent.csv* as a comparison dataset. 

### GLAKES Dataset
We also used information of the [GLAKES dataset](https://garslab.com/?p=234) as Li et al used the Information to update their maximum lake extents. 

This dataset was published in the article [Mapping global lake dynamics reveals the emerging roles of small lakes](https://www.nature.com/articles/s41467-022-33239-3)

## 01: Preprocessing
During the preprocessing we match the Hydrolakes dataset with the GWP data. This mapping helps us to match Global Water Pack with the chosen data for the product comparison. Many datasets use either Hydrolakes as a basis for their analysis, or we can use the Hydrolakes geometries to spatially join lakes from other datasets to GWP.

To get the preprocessing in the right order run:
01_run_hydrolakes_processing.py twice. Make sure your folder structure is the same as mentioned above: 

1. `uv run .\scripts\01_run_hydrolakes_processing.py --config .\configs\europe_hydrolakes.json`
 
2. `uv run .\scripts\01_run_hydrolakes_processing.py --config .\configs\world_hydrolakes.json`

This results in the following files: 
\Output\Hydrolakes\gwp_withHylaks_arlie.gpkg"
\Output\Hydrolakes\gwp_withHylaks_arlie_noMaxExtent.csv"
\Output\Hydrolakes\gwp_withHylaks_arlie_withMaxExtent.csv"
\Output\Hydrolakes\gwp_withHylaks_arlie_withMaxExtent.gpkg"
\Output\Hydrolakes\gwp_withHylaks_world.gpkg"
\Output\Hydrolakes\gwp_withHylaks_world_noMaxExtent.csv"
\Hydrolakes\gwp_withHylaks_world_withMaxExtent.csv"
\Output\Hydrolakes\gwp_withHylaks_world_withMaxExtent.gpkg"
\Output\Hydrolakes\hydrolakes_clipped_europe.gpkg"

Afterwards the preprocessing steps differ in respect to the corresponding dataset. 

### Arlie 

### Nasa Flood Product

### Global Lake Surface Extent (Li)

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