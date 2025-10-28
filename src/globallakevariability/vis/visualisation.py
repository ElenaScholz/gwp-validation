import matplotlib.pyplot as plt
import numpy as np
import math
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
from pypalettes import load_cmap
import pandas as pd
import matplotlib.dates as mdates
from highlight_text import ax_text


def plot_world_map(df, statistic_value, title, aggregation='mean', 
                            gridsize=30, plot_type='hexbin', cmap = load_cmap("Blue2Orange12Steps", cmap_type = "continuous"), save=False, 
                            out_dir=None, filename=None):
    '''
    Erstellt eine Weltkarte mit Hexbin oder Scatter-Darstellung statistischer Werte
    
    Parameters:
    -----------
    plot_type : str, default='hexbin'
        'hexbin' für Hexbin-Plot oder 'scatter' für Punktplot
    '''
    # Validation
    valid_aggregations = ['mean', 'max', 'min', 'count', 'median']
    if aggregation not in valid_aggregations:
        raise ValueError(f"Aggregation must be one of {valid_aggregations}")
    
    valid_plot_types = ['hexbin', 'scatter']
    if plot_type not in valid_plot_types:
        raise ValueError(f"plot_type must be one of {valid_plot_types}")
    cmap = cmap
    # Farblogik für Statistikwerte
    stat_config = {
        "R2": {"cmap": cmap, "vmin": 0, "vmax": 1, 
               "label": "R²"},
        "spearman_cor": {"cmap": cmap, "vmin": -1, "vmax": 1, 
                        "label": "spearman correlation"},
        "MAE": {"cmap": "viridis_r", "label": "MAE (0 = gut, hoch = schlecht)"},
        "RMSE": {"cmap": cmap.reversed(), "label": "RMSE"},
    }

    # Dynamic min/max
    if aggregation == 'count' and plot_type == 'hexbin':
        vmax = None
        vmin = 0
    else:
        data_min = df[statistic_value].min()
        data_max = df[statistic_value].max()
        vmin, vmax = data_min, data_max

    # Create figure
    fig = plt.figure(figsize=(14, 7), dpi=150)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson())
    ax.spines['geo'].set_visible(False)

    # Styling
    ax.add_feature(cfeature.LAND.with_scale('50m'), 
                   facecolor='#CCCCCC', edgecolor='none', zorder=0)
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), 
                   linewidth=0.5, edgecolor='#E5E5E5', zorder=1)
    ax.add_feature(cfeature.BORDERS.with_scale('50m'), 
                   linestyle=':', linewidth=0.7, edgecolor="white", zorder=1)
    
    ax.set_global()
    # Remove Antarctica-like behavior (optional: add extent limit)
    ax.set_extent([-180, 180, -60, 85], crs=ccrs.PlateCarree())

    # Colormap configuration
    base_cmap = 'coolwarm'
    if statistic_value in stat_config:
        cfg = stat_config[statistic_value]
        cmap = cfg.get("cmap", base_cmap)
        vmin = cfg.get("vmin", vmin)
        vmax = cfg.get("vmax", vmax)
        cbar_label = cfg.get("label", statistic_value)
    else:
        cmap = base_cmap
        cbar_label = statistic_value

    # Plot based on type
    if plot_type == 'hexbin':
        # Aggregation function
        if aggregation == 'mean':
            reduce_C_function = np.mean
        elif aggregation == 'median':
            reduce_C_function = np.median
        elif aggregation == 'max':
            reduce_C_function = np.max
        elif aggregation == 'min':
            reduce_C_function = np.min
        elif aggregation == 'count':
            reduce_C_function = len

        # Hexbin plot
        mappable = ax.hexbin(
            df['latitude'], df['longitude'],
            C=df[statistic_value] if aggregation != 'count' else None,
            gridsize=gridsize,
            reduce_C_function=reduce_C_function,
            cmap=cmap,
            alpha=0.8,
            linewidths=0.3,
            edgecolors='white',
            transform=ccrs.PlateCarree(),
            vmin=vmin,
            vmax=vmax,
            zorder=2
        )
        
    elif plot_type == 'scatter':
        # Scatter plot
        mappable = ax.scatter(
            df['latitude'], df['longitude'],
            c=df[statistic_value],
            cmap=cmap,
            s=20,
            alpha=0.6,
            edgecolors='none',
            transform=ccrs.PlateCarree(),
            vmin=vmin,
            vmax=vmax,
            zorder=2
        )

    # Colorbar
    plt.subplots_adjust(bottom=0.12, top=0.92, left=0.05, right=0.95)
    cax = fig.add_axes([0.2, 0.08, 0.6, 0.025])

    if vmax is None:
        vmax = int(mappable.get_array().max())
    ticks = np.linspace(vmin, vmax, 6)

    cbar = fig.colorbar(mappable, cax=cax, orientation='horizontal',
                        label=cbar_label, ticks=ticks)
    cbar.ax.tick_params(labelsize=9)

    # Title
    plot_title = f'{title} {statistic_value}'
    if plot_type == 'hexbin' and aggregation != 'mean':
        plot_title += f' ({aggregation})'
    ax.set_title(plot_title, fontsize=13, pad=10)

    # Save
    if save:
        if out_dir is None:
            raise ValueError("out_dir must be provided when save=True")
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = f"_{aggregation}" if plot_type == 'hexbin' else "scatter"
        output_path = out_dir / f"{filename}_{plot_type}{suffix}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')

    plt.close()

    # Statistics output
    print(f"Statistik für {statistic_value} (Plot: {plot_type}):")
    if plot_type == 'hexbin':
        if aggregation == 'count':
            print(f"Maximale Anzahl von Punkten in einem Hexagon: {mappable.get_array().max()}")
            print(f"Gesamtzahl der Hexagone: {len(mappable.get_array())}")
        else:
            print(f"Aggregation: {aggregation}")
    print(f"Minimum: {df[statistic_value].min():.4f}")
    print(f"Maximum: {df[statistic_value].max():.4f}")
    print(f"Mittelwert: {df[statistic_value].mean():.4f}")
    print(f"Anzahl der Datenpunkte: {len(df)}")


def plot_europe_map(df, statistic_value, title, aggregation='mean', 
                             gridsize=30, plot_type='hexbin', cmap = load_cmap("Blue2Orange12Steps", cmap_type = "continuous"), save=False, out_dir=None, filename = None):
    """
    Erstellt eine Europakarte mit Hexbin- oder Scatter-Darstellung
    NOW USES ROBINSON PROJECTION to match R plots
    """

    valid_aggregations = ['mean', 'max', 'min', 'count', 'median']
    if aggregation not in valid_aggregations:
        raise ValueError(f"Aggregation must be one of {valid_aggregations}")

    valid_plot_types = ['hexbin', 'scatter']
    if plot_type not in valid_plot_types:
        raise ValueError(f"plot_type must be one of {valid_plot_types}")

    if isinstance(save, str):
        save = save.lower() in ('true', '1', 'yes')

    # If aggregation requires a statistic column or if scatter is requested, ensure column exists
    if (aggregation != 'count' or plot_type == 'scatter') and statistic_value not in df.columns:
        print(f"Statistic '{statistic_value}' not found. Skipping plot.")
        return None

    # Handle column name variations
    lat_col = 'latitude' if 'latitude' in df.columns else 'Latitude' if 'Latitude' in df.columns else None
    lon_col = 'longitude' if 'longitude' in df.columns else 'Longitude' if 'Longitude' in df.columns else None
    
    if lat_col is None or lon_col is None:
        print("Latitude/Longitude columns not found. Skipping plot.")
        return None
    cmap = cmap

    # Farblogik
    stat_config = {
        "R2": {"cmap": cmap, "vmin": 0, "vmax": 1, 
               "label": r"R²"},
        "spearman_cor": {"cmap": cmap, "vmin": -1, "vmax": 1, 
                        "label": "spearman correlation"},
        "MAE": {"cmap": cmap, "label": "MAE (0 = gut, hoch = schlecht)"},
        # reverse cmap for error metrics

        "RMSE": {"cmap": cmap.reversed(), "label": "RMSE"},
    }

    if aggregation == 'count' and plot_type == 'hexbin':
        vmax = None
        vmin = 0
    else:
        data_min = df[statistic_value].min() if statistic_value in df.columns else 0
        data_max = df[statistic_value].max() if statistic_value in df.columns else 1
        vmin, vmax = data_min, data_max

    # CHANGED: Use Robinson projection like R function
    fig = plt.figure(figsize=(10, 8), dpi=150)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson())
    ax.spines['geo'].set_visible(False)
    # Styling to match R plots
    ax.add_feature(cfeature.LAND.with_scale('50m'), 
                   facecolor='#CCCCCC', edgecolor='none', zorder=0)
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), 
                   linewidth=0.5, edgecolor='#E5E5E5', zorder=1)
    ax.add_feature(cfeature.BORDERS.with_scale('50m'), 
                   linestyle=':', linewidth=0.7, edgecolor='#999999', zorder=1)

    # Europe extent in PlateCarree coordinates, then transformed by Robinson
    ax.set_extent([-25, 44, 36, 69], crs=ccrs.PlateCarree())

    # Colormap
    base_cmap = 'coolwarm'
    if statistic_value in stat_config:
        cfg = stat_config[statistic_value]
        cmap = cfg.get("cmap", cmap)
        vmin = cfg.get("vmin", vmin)
        vmax = cfg.get("vmax", vmax)
        cbar_label = cfg.get("label", statistic_value)
    else:
        cbar_label = statistic_value

    mappable = None

    # Aggregation function (only relevant for hexbin)
    if aggregation == 'mean':
        reduce_C_function = np.mean
    elif aggregation == 'median':
        reduce_C_function = np.median
    elif aggregation == 'max':
        reduce_C_function = np.max
    elif aggregation == 'min':
        reduce_C_function = np.min
    elif aggregation == 'count':
        reduce_C_function = len

    # Plot based on type
    if plot_type == 'hexbin':
        mappable = ax.hexbin(
            df[lat_col], df[lon_col],
            C=df[statistic_value] if aggregation != 'count' else None,
            gridsize=gridsize,
            reduce_C_function=reduce_C_function,
            cmap=cmap,
            alpha=0.8,
            linewidths=0.5,
            edgecolors='white',
            transform=ccrs.PlateCarree(),
            vmin=vmin,
            vmax=vmax,
            zorder=2
        )
    else:  # scatter
        mappable = ax.scatter(
            df[lat_col], df[lon_col],
            c=df[statistic_value],
            cmap=cmap,
            s=20,
            alpha=0.6,
            edgecolors='none',
            transform=ccrs.PlateCarree(),
            vmin=vmin,
            vmax=vmax,
            zorder=2
        )

    # Colorbar
    plt.subplots_adjust(bottom=0.12, top=0.92, left=0.05, right=0.95)
    cax = fig.add_axes([0.2, 0.08, 0.6, 0.025])
    
    if vmax is None and hasattr(mappable, "get_array"):
        try:
            vmax = int(mappable.get_array().max())
        except Exception:
            vmax = 1
    ticks = np.linspace(vmin, vmax, 6)

    cbar = fig.colorbar(mappable, cax=cax, orientation='horizontal', 
                       label=cbar_label, ticks=ticks)
    cbar.ax.tick_params(labelsize=9)

    # Title
    plot_title = f'{title} {statistic_value}'
    if plot_type == 'hexbin' and aggregation != 'mean':
        plot_title += f' ({aggregation})'
    ax.set_title(plot_title, fontsize=13, pad=10)

    if save:
        if out_dir is None:
            raise ValueError("out_dir must be provided when save=True")
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = f"_{aggregation}" if plot_type == 'hexbin' else "_scatter"
        output_path = out_dir / f"{filename}_{plot_type}{suffix}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')

    plt.close()

    # Statistics
    print(f"Statistik für {statistic_value} (Plot: {plot_type}):")
    if plot_type == 'hexbin':
        if aggregation == 'count':
            print(f"Maximale Anzahl von Punkten in einem Hexagon: {mappable.get_array().max()}")
            print(f"Gesamtzahl der Hexagone: {len(mappable.get_array())}")
        else:
            print(f"Aggregation: {aggregation}")
    if statistic_value in df.columns:
        print(f"Minimum: {df[statistic_value].min():.4f}")
        print(f"Maximum: {df[statistic_value].max():.4f}")
        print(f"Mittelwert: {df[statistic_value].mean():.4f}")
    print(f"Anzahl der Datenpunkte: {len(df)}")


def quick_monthly_plot(*datasets_and_titles, figwidth=14, subplot_height=3.5):
    colors = ["#1B9E77", "#D95F02", "#7570B3"] 
    plt.rcParams['figure.dpi'] = 300
    
    n_plots = len(datasets_and_titles)
    if n_plots == 0:
        print("Keine Datasets übergeben!")
        return
    
    fig_height = subplot_height * n_plots
    fig, ax = plt.subplots(nrows=n_plots, figsize=(figwidth, fig_height))
    if n_plots == 1:
        ax = [ax]
    
    for i, (df, title) in enumerate(datasets_and_titles):
        if "Date" in df.columns:
            df = df.copy()
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date")
        df = df.sort_index()
        
        # GWP Plot
        if "GWP_Area_km2" in df.columns:
            ax[i].plot(df.index, df["GWP_Area_km2"], 
                       label='GWP', color=colors[0], linewidth=2)
        
        # Li Plot
        if "Li_Area_m2" in df.columns:
            ax[i].plot(df.index, df["Li_Area_m2"], 
                       label='Li et al', color=colors[1], linewidth=2)

        # ---- Frozen Tag einbauen ----
        if "Li_Frozen_Tag" in df.columns:
            frozen_periods = df[df["Li_Frozen_Tag"] == True]
            if not frozen_periods.empty:
                # Variante 1: Marker auf Li-Kurve
                ax[i].scatter(frozen_periods.index, frozen_periods["Li_Area_m2"],
                              color="blue", s=20, label="Frozen", zorder=5, alpha=0.7)
                
                # Variante 2: Hintergrund einfärben
                for t in frozen_periods.index:
                    ax[i].axvspan(t - pd.Timedelta(days=15), 
                                  t + pd.Timedelta(days=15),
                                  color="lightblue", alpha=0.2)

        # Styling
        ax[i].set_title(title, fontsize=12, fontweight='bold')
        ax[i].legend()
        ax[i].grid(True, alpha=0.3)
        ax[i].set_ylabel('Surface Area (km²)')
        ax[i].spines[["top", "right"]].set_visible(False)
        ax[i].xaxis.set_major_locator(mdates.YearLocator(2))
        ax[i].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax[i].tick_params(axis='x', rotation=45)
        if i == n_plots - 1:
            ax[i].set_xlabel('Year')
    
    plt.tight_layout()
    plt.show()


# Funktionen für häufige Fälle 
def plot_two_lakes(df1, title1, df2, title2): 
    quick_monthly_plot((df1, title1), (df2, title2)) 
def plot_three_lakes(df1, title1, df2, title2, df3, title3): 
    quick_monthly_plot((df1, title1), (df2, title2), (df3, title3)) 
def plot_four_lakes(df1, title1, df2, title2, df3, title3, df4, title4): 
    quick_monthly_plot((df1, title1), (df2, title2), (df3, title3), (df4, title4)) 
def plot_5_lakes(df1, title1, df2, title2, df3, title3, df4, title4, df5, title5): 
    quick_monthly_plot((df1, title1), (df2, title2), (df3, title3), (df4, title4), (df5, title5))

