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
ROOT = Path(r"T:\DLR\Analysis3\Results_10percDisr")
OUTPUT_DIR = Path(r"T:\DLR\Analysis3\Maps_10percDisr_colors")
os.makedirs(OUTPUT_DIR, exist_ok=True)
statistic_values_to_plot = ["spearman_cor", "RMSE"]
save_tag = "True"

# # Read in all files of the folder
# files = list(ROOT.glob("*.csv"))

# statistic_data = {}
# for file in files: 
#     statistic_data[file.stem] = pd.read_csv(file)




# arlie = (statistic_data['arlie_stats_df'], statistic_data['arlie_stats_df_z'])
# nasa = (statistic_data['nasa_stats_df'], statistic_data['nasa_stats_df_z'])
# li = (statistic_data['li_stats_df'], statistic_data['li_stats_df_z'])
# li_no_frozen = (statistic_data['li_stats_df_no_frozen'], statistic_data['li_stats_df_no_frozen_z'])

# arlie_plots = []
# nasa_plots = []
# li_plots = []
# for ds in arlie:
#     columnnames = ds.columns

#     if "gwp_mean_z" in columnnames:
#         plottitle = "Arlie - Z-Score - "
#     else:
#         plottitle = "Arlie - "

#     for stat in statistic_values_to_plot:
#         filename = f"{plottitle}{stat}"
#         p = plot_europe_map(ds, stat, aggregation='median', gridsize=50, plot_type = "scatter", cmap = cmap, save=save_tag, out_dir=OUTPUT_DIR, filename=filename) 
#         arlie_plots.append(p)


# for ds in nasa:
#     columnnames = ds.columns

#     if "gwp_mean_z" in columnnames:
#         plottitle = "Nasa - Z-Score - "
#     else:
#         plottitle = "Nasa - "


#     for stat in statistic_values_to_plot:
#         filename = f"{plottitle}{stat}"

#         p = plot_world_map(ds, stat, aggregation='median', gridsize=50, plot_type="scatter", cmap = cmap, save=save_tag, out_dir=OUTPUT_DIR, filename = filename ) 
#         nasa_plots.append(p)

# for ds in li:
#     columnnames = ds.columns

#     if "gwp_mean_z" in columnnames:
#         plottitle = "Li - Z-Score - "
#     else:
#         plottitle = "Li - "
#     print(plottitle)
#     for stat in statistic_values_to_plot:
#         filename = f"{plottitle}{stat}"
#         p = plot_world_map(ds, stat, aggregation='median', gridsize=50, plot_type = "scatter", cmap = cmap, save=save_tag, out_dir=OUTPUT_DIR, filename = filename ) 
#         li_plots.append(p)

# for ds in li_no_frozen:
#     columnnames = ds.columns

#     if "gwp_mean_z" in columnnames:
#         plottitle = "Li No Frozen - Z-Score - "
#     else:
#         plottitle = "Li No Frozen - "
#     print(plottitle)
#     for stat in statistic_values_to_plot:
#         filename = f"{plottitle}{stat}"
#         p = plot_world_map(ds, stat, aggregation='median', gridsize=50, plot_type = "scatter", cmap = cmap, save=save_tag, out_dir=OUTPUT_DIR, filename = filename ) 
#         li_plots.append(p)



# Read in all files of the folder
files = list(ROOT.glob("*.csv"))

statistic_data = {}
for file in files: 
    statistic_data[file.stem] = pd.read_csv(file)

print(statistic_data.keys())
arlie = (statistic_data['arlie_stats_df'], statistic_data['arlie_stats_df_z'])
nasa = (statistic_data['nasa_stats_df'], statistic_data['nasa_stats_df_z'])
li = (statistic_data['li_stats_df'], statistic_data['li_stats_df_z'])
li_no_frozen = (statistic_data['li_stats_df_no_frozen'], statistic_data['li_stats_df_z_no_frozen'])

def plot_dataset(datasets, base_name, plot_function):
    """
    Plot function that generates 3 plots per dataset:
    - 1 spearman correlation from non-z-transformed data
    - 2 RMSE plots (one from non-z, one from z-transformed)
    """
    plots = []
    
    # datasets[0] = non-z-transformed
    # datasets[1] = z-transformed
    
    # Plot 1: Spearman correlation from non-z-transformed data
    ds_non_z = datasets[0]
    filename = f"{base_name} - spearman_cor"
    p = plot_function(ds_non_z, "spearman_cor", aggregation='median', 
                      gridsize=50, plot_type="scatter", cmap=cmap, 
                      save=save_tag, out_dir=OUTPUT_DIR, filename=filename)
    plots.append(p)
    
    # Plot 2: RMSE from non-z-transformed data
    filename = f"{base_name} - RMSE"
    p = plot_function(ds_non_z, "RMSE", aggregation='median', 
                      gridsize=50, plot_type="scatter", cmap=cmap, 
                      save=save_tag, out_dir=OUTPUT_DIR, filename=filename)
    plots.append(p)
    
    # Plot 3: RMSE from z-transformed data
    ds_z = datasets[1]
    filename = f"{base_name} - Z-Score - RMSE"
    p = plot_function(ds_z, "RMSE", aggregation='median', 
                      gridsize=50, plot_type="scatter", cmap=cmap, 
                      save=save_tag, out_dir=OUTPUT_DIR, filename=filename)
    plots.append(p)
    
    return plots

# Generate plots for each dataset
arlie_plots = plot_dataset(arlie, "Arlie", plot_europe_map)
nasa_plots = plot_dataset(nasa, "Nasa", plot_world_map)
li_plots = plot_dataset(li, "Li", plot_world_map)
li_no_frozen_plots = plot_dataset(li_no_frozen, "Li No Frozen", plot_world_map)

print(f"Generated {len(arlie_plots)} plots for Arlie")
print(f"Generated {len(nasa_plots)} plots for Nasa")
print(f"Generated {len(li_plots)} plots for Li")
print(f"Generated {len(li_no_frozen_plots)} plots for Li No Frozen")
print(f"Total plots: {len(arlie_plots) + len(nasa_plots) + len(li_plots) + len(li_no_frozen_plots)}")