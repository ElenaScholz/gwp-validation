# DLR-GWPIntercomparison

# Folder Structure
Each Processing step was assigend to a number:  

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
│   ├──   
│   └──   
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
