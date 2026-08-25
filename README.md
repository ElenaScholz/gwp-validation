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

3. To activate the environment, run: `source .venv/Scripts/activate`. This needs to be done before running a script from the terminal

### pixi
1. If you don't habe pixi installed yet, follow the official guide: [pixi installation guide](https://pixi.sh/dev/installation/)  

2. To set up the envirnment, run `pixi sync` in your terminal.  

## About Paths
This code was developed on a Windows machine with windows 11

# Repository Structure
Each Processing step was assigend to a number:  

00 = Datadownload   
01 = Preprocessing  
02 = Matching GWP with a validation Dataset/Hydrolakes  
03 = calculate statistics  
04 = visualisation  


GlobalWaterPack_Product_Intercomparison/  
├── configs/  
│   ├── arlie.json  
│   ├── lse.json  
│   ├── nrt-fp.json  
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
│   ├── LSE  
│   │   ├── 01.1_matchGlakesHydrolakesGWP.py  
│   │   ├── 01.2_reshapeMonthly_LiLSE.py  
│   │   ├── 01.3_reshape_monthlyGWP.py   
│   ├── NRT-FP  
│   │   ├── 00_Download_GWP_raster.py        
│   │   ├── 01.1_clip_GWP_to_tiles.py  
│   │   ├── 01.2_NRT-FP_extractHDF.py      
│   │   ├── 01.3_run_GWP_NRT-FP_calculate_zonal_statistics.py    
│   ├── 01_run_hydrolakes_processing.py   
│   └── 02_run_match_arlie_complete.py    
│   └── 02_run_match_GWP_NRT-FP.py  
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
│   ├── LSE  
│   │   ├── GLAKES  
│   │   ├── Glakes_Prepared  
│   │   ├── Monthly_Lakes  
│   │   └── monthly_lake_surface_extent.csv    
│   ├── NRT-FP  
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
│   ├── LSE  
│   ├── NRT-FP    
├── Results  
├── Maps  
└── Plots  

**Note: The configuration files stored within the reporitory display the same folder structure, and if you don't change it, you just need to adjust the Root-directory**

# Workflow
The workflow follows the described steps within the paper. An overview is depicted in the flowchart below:

![Flowchart](images/FlowChartGWPvalidation.png)

## Data download 
### Hydrolakes
Download the Hydrolakes as polygons in Shapefile-Format from this website [Hydrolakes](https://www.hydrosheds.org/products/hydrolakes#downloads). 

Place the whole folder inside the HydroLAKES_polys_v10 folder. This folder is located in the Input-Folder.

### [Aggregated River and Lake Ice Extent (ARLIE)](https://doi.org/10.2909/5752e8b5-ecda-4013-8eb9-e27f8515b87e)
1. Download the ARLIE dataset for the whole time series (2016/09-2024). You can use the Script: *00_arlie_download_hda_files.py*

Our Area of Interest was the whole Area covered by ARLIE (Bounding Box: 69.00 N, 36.00S, 44.00E, -25.00W)

You can download a file called arlie_bbox.gpkg. Please move it inside the Input/Arlie folder

Note that the Area of interest needs to be **geopackage file** and that you need login credential to WEkEO for the hda-file donwload. 

[Registration](https://data.wekeo.copernicus.eu/register)

[Information about the Dataset](https://www.eea.europa.eu/en/datahub/datahubitem-view/b5c68a06-5dcf-42e5-baad-94f861189f91). 

Please download geometries as well as timeseries files. 

2. Afterwards the files need to be unzipped. To do so use the script: *00_extract_arlie_zipfiles.py* 

The files were downloaded on 01.04.2025. Later downloads may result in a differnt number of lakes, or dataset properties can change. 
Publication Date for this version was 2025-03-05, edition 01.00


### [Global Water Pack Raster (GWP)](https://geoservice.dlr.de/web/datasets/gwp_modis_p1d)

Global Water Pack comes as global raster datasets. The raster layers are needed for the NRT-FP comparison.

Those can be downloaded with the script `NRT-FP/00_Download_GWP_raster.py`.

Download the rasterfiles into this folder: \Input\NRT-FP\01_GlobalGWP 


**Note:** For the comparison with ARLIE as well as LSE we used already processed time series dataset containing daily Lake Area information in km², as well as coordinates for each lake in form of latitude/longitude information.
The information is stored in two corresponding files: one containing coordinates, one the time series.  

Furthermore we removed the 29.02. for all leap years. 

### [Near realtime Flood Product (NRT-FP)](https://www.earthdata.nasa.gov/data/instruments/viirs/near-real-time-data/nrt-global-flood-products)

The [near realtime global Flood Product](https://www.earthdata.nasa.gov/data/instruments/viirs/near-real-time-data/nrt-global-flood-products) provided by NASA is online available for recent years. We used historical data provided by NASA for the years 2010 and 2021. The datasets are in the folder "T:\GlobalWaterPack_Product_Intercomparison\INPUT\NRT-FP\01_NRT-FP"

### [Global Lake Surface Extent dataset (LSE)](https://zenodo.org/records/15536395)

The Global Lake Surface Extent dataset was published in mid 2025 within the paper [Global dominance of seasonality in shaping lake-surface-extent dynamics](https://www.nature.com/articles/s41586-025-09046-3#data-availability) by Li et al. 

Data is available [here](https://zenodo.org/records/15536395)
We used the *monthly_lake_surface_extent.csv* version 7 as a comparison dataset. 

### [GLAKES Dataset](https://garslab.com/?p=234)
We also used information of the [GLAKES dataset](https://garslab.com/?p=234) as Li et al used the Information to update their maximum lake extents. 

This dataset was published in the article [Mapping global lake dynamics reveals the emerging roles of small lakes](https://www.nature.com/articles/s41467-022-33239-3)

## 01: Preprocessing
During the preprocessing we match the Hydrolakes dataset with the GWP data. This mapping helps us to match Global Water Pack with the chosen data for the product comparison. Many datasets use either Hydrolakes as a basis for their analysis, or we can use the Hydrolakes geometries to spatially join lakes from other datasets to GWP.

To get the preprocessing in the right order run:
01_run_hydrolakes_processing.py twice (once for europe and once for a global analysis). Make sure your folder structure is the same as mentioned above: 


1. `uv run .\scripts\01_run_hydrolakes_processing.py --config .\configs\europe_hydrolakes.json`
 
2. `uv run .\scripts\01_run_hydrolakes_processing.py --config .\configs\world_hydrolakes.json`

**This results in the following files:**  
\Output\Hydrolakes\gwp_withHylaks_arlie.gpkg  
\Output\Hydrolakes\gwp_withHylaks_arlie_noMaxExtent.csv
\Output\Hydrolakes\gwp_withHylaks_arlie_withMaxExtent.csv
\Output\Hydrolakes\gwp_withHylaks_arlie_withMaxExtent.gpkg
\Output\Hydrolakes\gwp_withHylaks_world.gpkg
\Output\Hydrolakes\gwp_withHylaks_world_noMaxExtent.csv
\Hydrolakes\gwp_withHylaks_world_withMaxExtent.csv
\Output\Hydrolakes\gwp_withHylaks_world_withMaxExtent.gpkg
\Output\Hydrolakes\hydrolakes_clipped_europe.gpkg

Afterwards the preprocessing steps differ in respect to the corresponding dataset. 

### 01 NRT-FP

1. The Global Water Pack Raster Datasets need to be clipped to the extent of the Nasa Flood Product tiles. This can be done through the script `01.1_clip_GWP_to_tiles.py`. 

**Input:**  
The Global Water Pack raster all lie within one directory, to which they were downloaded. 
\Input\NRT-FP\01_GlobalGWP\GWP.OSWF.DAILY.20100101.v1.tif  
\Input\NRT-FP\01_GlobalGWP\GWP.OSWF.DAILY.20100102.v1.tif  
\Input\NRT-FP\01_GlobalGWP\GWP.OSWF.DAILY.20100103.v1.tif  
\Input\NRT-FP\01_GlobalGWP\....tif  
...   

**Output:**  
As you can see below the output results in one folder per MODIS tile with all corresponding raster files for all used years.   
\Input\NRT-FP\02_GWP-tiles\h06v04\GWP.OSWF.DAILY.20100101.h06v04.tif  
\Input\NRT-FP\02_GWP-tiles\h06v04\GWP.OSWF.DAILY.20100102.h06v04.tif  
\Input\NRT-FP\02_GWP-tiles\h08v05  
...  


2. The NRT-FP comes in hdf-fileformat. To extract the datasets use the script *01.2_NRT-FP_extract_HDF.py* in the terminal: 

`pixi run python .\scripts\NRT-FP\01.2_NRT-FP_extract_HDF.py --config .\configs\nrt-fp.json`

**Input:**  
The Nasa Flood Product tiles are stored within a folder per tile and year.
\Input\NRT-FP\01_MWP\MCDWD.h06v04.2010  
\Input\NRT-FP\01_MWP\MCDWD.h06v04.2021  
...  

**Output:**  
The Output folder follow the same structure stored within a different folder. 
\Input\NRT-FP\02_MWP_gtiff\MCDWD.h06v04.2010  
\Input\NRT-FP\02_MWP_gtiff\MCDWD.h06v04.2021  
...  

3. **Calculate the zonal statistics** as a last step of preprocessing for the Nasa Flood Product. 

`uv run python .\scripts\NRT-FP\01.3_run_GWPNRT-FP_calculate_zonalStatistics.py --config .\configs\nrt-fp.json`

**Input:**
- The tiff files for GWP and Nasa Flood Product generated with the steps above. 
- the max_extent_tiles (/Input/NRT-FP/max_extent_tiles)
- adjust the chunk size, number of workers etc to your needs in the config file *nrt-fp.json*

**Output:**
The results are stored in this folder *\Output\NRT-FP*. They are in .csv format.

### 01 Global Lake Surface Extent (Li)

1. match Glakes with Hydrolakes and GWP
We match the Glakes geometries with Hydrolakes geometries. We use all Lakes that overlap with a minimum area of 30%. Then we keep all intersecting lakes, where there is a 1:1 match or were multiple Hydrolakes are assigend to one Lake of the Glakes dataset. All other matches lead to the exclusion of samples. 

For more information check out the *GLAKESProcessir.py* and the *postprocessingGlakes.py* files. 

`uv run python .\scripts\Li\01.1_matchGlakesHydrolakesGWP.py --config .\configs\li.json`

**Input:**  
- Output/Hydrolakes/gwp_withHylaks_world_withMaxExtent.gpkg  
- Input/HydroLAKES_polys_v10/hydrolakes_poly_greater20m.gpkg - generate this file by removing all lakes with an area smaller then 20km²  
- Input/Li/GLAKES/GLAKES/GLAKES

**Output:**
Outputs are stored within this directory: 
Input\Li\Glakes_Prepared  
\Input\Li\Glakes_Prepared\glakes_hylak_30_subset.gpkg  
\Input\Li\Glakes_Prepared\gwp_glakes_hylak_30_merged_strict.gpkg  

2. reshape the Lake Surface Extent file from Li et al. 
This script reshaped the wide dataframe format of the Li dataset into Long. 

`uv run python .\scripts\Li\01.2_reshapeMonthly_LiLSE.py --config .\configs\li.json`

**Input:**
\Input\Li\monthly_lake_surface_extent.csv  
**Output:**
- \Input\Li\monthly_lake_surface_extent_long.csv  

3. reshape the GWP timeseries to monthly medians

As GWP Timeseries contains daily information this script calculates monthly medians for each lake.

**Input:**  
A folder *\Input\GWP\05_timeseries_8247_rm2902* with daily timeseries
**Output:**
A folder *\Input\GWP\06_timeseries_8247_rm2902_monthly_hylakIDs* with monthly timeseries
  
## 02 Matching Global Waterpack with validation Datasets
### ARLIE

`uv run .\scripts\02_run_match_arlie_complete.py --config .\configs\arlie.json`

This script contains two subscripts saved in the arlie folder:
1. 02.1_run_arlie_gwp_geom_matching.py
2. 02.2_run_arlie_gwp_ts_matching.py

The first script joins all Arlie geometries spatially with Hydrolakes geometries created in the Script 01_run_hydrolakes. 

Then the Arlie timeseries information is matched.


In the second script the gwp timeseries information is matched. The following checks are made:
- Checking for Lake Area differences of more then 10%
- Filtering out all dates where ARLIE has a disruption (Cloud Coverage + Other entities + XX) higher then 10%
- removing lakes with less then 5% matching data-coverage. 


**Input:** 
gwp_hydrolakes_max_extent
path to unzipped arlie files

**Output:** 
csv files for each gwp sample with in arlie aoi. 
containing the arlie timeseries + max extent information + gwp id 

### Nasa Flood Product
Use the Script *02_run_match_GWP_NRT-FP.py* to match Nasa Flood Product timeseries with GWP timeseries. 

`uv run python .\scripts\02_run_match_GWP_NRT-FP.py --config .\configs\nrt-fp.json` 

### Monthly Lake Surface Area by Li et al.

Run the Scripts 02.1_run_matchGWPandLiByGlakes.py as well as 02.2_run_LiProcessData.py.

`uv run python .\scripts\02.1_run_matchGWPandLiByGlakes.py --config .\configs\li.json` 
`uv run python .\scripts\02.2_run_LiProcessData.py --config .\configs\li.json` 

## Statistics
The statistics script uses the stats.json as a config file. 
In this script the lake areas are all calculated in % and will be z-transformed.  
The RMSE as well as spearman correlation are calculated.  

**Input:**  
"li_data_strict" : "Output/allValidationDatasets/LiData/Li_all_lakes_strict_no_frozen.csv",  
"li_data_no_frozen" : "Output/allValidationDatasets/LiData/Li_all_lakes_no_frozen.csv",  
"arlie_data": "Output/AllValidationDatasets/Arlie_len146/all_arlie_lakes_10percDisr_len146.csv",  
"NRT-FP_data": "Output/AllValidationDatasets/NRT-FP/all_lakes_percentage_10percDisr.csv",  
"hydrolakes": "Output/Hydrlakes/gwp_withHylaksAndMaxExtent_world.gpkg"  

**Output:**  
All outputs will be stored within the Results output directory (Results_10percDisr):  
Results_10percDisr\all_stats_df.csv  
Results_10percDisr\arlie_stats_df.csv  
Results_10percDisr\arlie_stats_df_z.csv  
Results_10percDisr\li_stats_df.csv  
Results_10percDisr\li_stats_df_no_frozen.csv  
Results_10percDisr\li_stats_df_z.csv  
Results_10percDisr\li_stats_df_z_no_frozen.csv  
Results_10percDisr\nasa_stats_df.csv  
Results_10percDisr\nasa_stats_df_z.csv  
Results_10percDisr\stats_summary_compact.csv  

To run the script use to following command in the terminal.  
`uv run python .\scripts\03_calculateStatistics.py --config .\configs\stats.json` 

## Visualisations
Final results will be displayed in form of maps. The used script is named `04_plotMaps.py`

The final results will look like this:   
![Worldmap global LSE extent (Li et al. 2025)](images/LiRMSE_scatterscatter.tif)

# Sources
- [Global dominance of seasonality in shaping lake-surface-extent dynamics](https://www.nature.com/articles/s41586-025-09046-3)  
- [global LSE Dataset](https://zenodo.org/records/15536395)  
- [near realtime global Flood Product](https://www.earthdata.nasa.gov/data/instruments/viirs/near-real-time-data/nrt-global-flood-products)  
- [Hydrolakes](https://www.hydrosheds.org/products/hydrolakes#downloads).   
- [ARLIE](https://www.eea.europa.eu/en/datahub/datahubitem-view/b5c68a06-5dcf-42e5-baad-94f861189f91).  
- [GLAKES dataset](https://garslab.com/?p=234)  
- [Mapping global lake dynamics reveals the emerging roles of small lakes](https://www.nature.com/articles/s41467-022-33239-3)  
