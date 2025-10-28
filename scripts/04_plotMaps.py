import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from highlight_text import ax_text
import os
from globallakevariability.vis.visualisation import plot_world_map, plot_europe_map
from pypalettes import load_cmap
cmap = load_cmap("Blue2Orange12Steps", cmap_type = "continuous")
ROOT = Path(r"T:\DLR\Analysis3\Results")
OUTPUT_DIR = Path(r"T:\DLR\Analysis3\Maps")
os.makedirs(OUTPUT_DIR, exist_ok=True)
statistic_values_to_plot = ["spearman_cor", "R2", "RMSE"]
save_tag = "True"

# Read in all files of the folder
files = list(ROOT.glob("*.csv"))

statistic_data = {}
for file in files: 
    statistic_data[file.stem] = pd.read_csv(file)

arlie = (statistic_data['arlie_stats_df'], statistic_data['arlie_stats_df_z'])
nasa = (statistic_data['nasa_stats_df'], statistic_data['nasa_stats_df_z'])
li = (statistic_data['li_stats_df'], statistic_data['li_stats_df_z'])


arlie_plots = []
nasa_plots = []
li_plots = []
for ds in arlie:
    columnnames = ds.columns

    if "gwp_mean_z" in columnnames:
        plottitle = "Arlie - Z-Score - "
    else:
        plottitle = "Arlie - "

    for stat in statistic_values_to_plot:
        filename = f"{plottitle}{stat}"
        p = plot_europe_map(ds, stat, plottitle, aggregation='median', gridsize=50, plot_type = "scatter", cmap = cmap, save=save_tag, out_dir=OUTPUT_DIR, filename=filename) 
        arlie_plots.append(p)


for ds in nasa:
    columnnames = ds.columns

    if "gwp_mean_z" in columnnames:
        plottitle = "Nasa - Z-Score - "
    else:
        plottitle = "Nasa - "


    for stat in statistic_values_to_plot:
        filename = f"{plottitle}{stat}"

        p = plot_world_map(ds, stat, plottitle, aggregation='median', gridsize=50, plot_type="scatter", cmap = cmap, save=save_tag, out_dir=OUTPUT_DIR, filename = filename ) 
        nasa_plots.append(p)

for ds in li:
    columnnames = ds.columns

    if "gwp_mean_z" in columnnames:
        plottitle = "Li - Z-Score - "
    else:
        plottitle = "Li - "
    print(plottitle)
    for stat in statistic_values_to_plot:
        filename = f"{plottitle}{stat}"
        p = plot_world_map(ds, stat, plottitle, aggregation='median', gridsize=50, plot_type = "scatter", cmap = cmap, save=save_tag, out_dir=OUTPUT_DIR, filename = filename ) 
        li_plots.append(p)


