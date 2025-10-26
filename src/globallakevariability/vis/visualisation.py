import matplotlib.pyplot as plt
import numpy as np
import math
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
from pathlib import Path
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np


def geographic_world_hexbin(df, statistic_value, title, aggregation='mean', 
                            gridsize=30, save=False, out_dir=None):
    '''
    Erstellt eine Weltkarte mit Hexbin-Darstellung statistischer Werte
    Aligned with R Robinson projection style
    '''
    # Validation
    valid_aggregations = ['mean', 'max', 'min', 'count', 'median']
    if aggregation not in valid_aggregations:
        raise ValueError(f"Aggregation must be one of {valid_aggregations}")

    # Farblogik für Statistikwerte
    stat_config = {
        "R2": {"cmap": "viridis", "vmin": 0, "vmax": 1, 
               "label": r"$R^2$ (1 = gut, 0 = schlecht)"},
        "spearman_cor": {"cmap": "coolwarm", "vmin": -1, "vmax": 1, 
                        "label": r"Spearman $\rho$ (-1..1)"},
        "MAE": {"cmap": "viridis_r", "label": "MAE (0 = gut, hoch = schlecht)"},
        "RMSE": {"cmap": "viridis_r", "label": "RMSE (0 = gut, hoch = schlecht)"},
    }

    # Dynamic min/max
    if aggregation == 'count':
        vmax = None
        vmin = 0
    else:
        data_min = df[statistic_value].min()
        data_max = df[statistic_value].max()
        vmin, vmax = data_min, data_max

    # Create figure with aspect ratio closer to R's ggplot output
    fig = plt.figure(figsize=(14, 7), dpi=150)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson())

    # Styling to match R: simple gray land, thin borders
    ax.add_feature(cfeature.LAND.with_scale('50m'), 
                   facecolor='#CCCCCC', edgecolor='none', zorder=0)
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), 
                   linewidth=0.5, edgecolor='#E5E5E5', zorder=1)
    ax.add_feature(cfeature.BORDERS.with_scale('50m'), 
                   linestyle=':', linewidth=0.7, edgecolor="white", zorder=1)
    
    # Set global extent (Robinson handles this well)
    ax.set_global()
    
    # Remove Antarctica-like behavior (optional: add extent limit)
    # ax.set_extent([-180, 180, -60, 85], crs=ccrs.PlateCarree())

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

    # Hexbin with adjusted styling
    hexbin = ax.hexbin(
        df['latitude'], df['longitude'],
        C=df[statistic_value] if aggregation != 'count' else None,
        gridsize=gridsize,
        reduce_C_function=reduce_C_function,
        cmap=cmap,
        alpha=0.8,  # Slightly more opaque
        linewidths=0.3,  # Thinner edges to match R style
        edgecolors='white',  # White edges for cleaner look
        transform=ccrs.PlateCarree(),
        vmin=vmin,
        vmax=vmax,
        zorder=2
    )

    # Colorbar with better positioning
    plt.subplots_adjust(bottom=0.12, top=0.92, left=0.05, right=0.95)
    cax = fig.add_axes([0.2, 0.08, 0.6, 0.025])

    if vmax is None:
        vmax = int(hexbin.get_array().max())
    ticks = np.linspace(vmin, vmax, 6)

    cbar = fig.colorbar(hexbin, cax=cax, orientation='horizontal',
                        label=cbar_label, ticks=ticks)
    cbar.ax.tick_params(labelsize=9)

    # Title with consistent styling
    plot_title = f'{title} {statistic_value}'
    if aggregation != 'mean':
        plot_title += f' ({aggregation})'
    ax.set_title(plot_title, fontsize=13, pad=10)

    # Save
    if save:
        if out_dir is None:
            raise ValueError("out_dir must be provided when save=True")
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / f"mfp_gwp_geographic_hexbin_{statistic_value}_{aggregation}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')

    plt.close()

    # Statistics output
    print(f"Statistik für {statistic_value} (Aggregation: {aggregation}):")
    if aggregation == 'count':
        print(f"Maximale Anzahl von Punkten in einem Hexagon: {hexbin.get_array().max()}")
        print(f"Gesamtzahl der Hexagone: {len(hexbin.get_array())}")
    else:
        print(f"Minimum: {df[statistic_value].min():.4f}")
        print(f"Maximum: {df[statistic_value].max():.4f}")
        print(f"Mittelwert: {df[statistic_value].mean():.4f}")
        print(f"Anzahl der Datenpunkte: {len(df)}")


def geographic_europe_hexbin(df, statistic_value, title, aggregation='mean', 
                             gridsize=30, save=False, out_dir=None):
    """
    Erstellt eine Europakarte mit Hexbin-Darstellung
    NOW USES ROBINSON PROJECTION to match R plots
    """
    valid_aggregations = ['mean', 'max', 'min', 'count', 'median']
    if aggregation not in valid_aggregations:
        raise ValueError(f"Aggregation must be one of {valid_aggregations}")

    if isinstance(save, str):
        save = save.lower() in ('true', '1', 'yes')

    if aggregation != 'count' and statistic_value not in df.columns:
        print(f"Statistic '{statistic_value}' not found. Skipping plot.")
        return None

    # Handle column name variations
    lat_col = 'latitude' if 'latitude' in df.columns else 'Latitude'
    lon_col = 'longitude' if 'longitude' in df.columns else 'Longitude'
    
    if lat_col not in df.columns or lon_col not in df.columns:
        print("Latitude/Longitude columns not found. Skipping plot.")
        return None

    # Farblogik
    stat_config = {
        "R2": {"cmap": "viridis", "vmin": 0, "vmax": 1, 
               "label": r"$R^2$ (1 = gut, 0 = schlecht)"},
        "spearman_cor": {"cmap": "coolwarm", "vmin": -1, "vmax": 1, 
                        "label": r"Spearman $\rho$ (-1..1)"},
        "MAE": {"cmap": "viridis_r", "label": "MAE (0 = gut, hoch = schlecht)"},
        "RMSE": {"cmap": "viridis_r", "label": "RMSE (0 = gut, hoch = schlecht)"},
    }

    if aggregation == 'count':
        vmax = None
        vmin = 0
    else:
        data_min = df[statistic_value].min()
        data_max = df[statistic_value].max()
        vmin, vmax = data_min, data_max

    # CHANGED: Use Robinson projection like R function
    fig = plt.figure(figsize=(10, 8), dpi=150)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson())
    
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
        cmap = cfg.get("cmap", base_cmap)
        vmin = cfg.get("vmin", vmin)
        vmax = cfg.get("vmax", vmax)
        cbar_label = cfg.get("label", statistic_value)
    else:
        cmap = base_cmap
        cbar_label = statistic_value

    # Aggregation
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

    # Hexbin
    hexbin = ax.hexbin(
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

    # Colorbar
    plt.subplots_adjust(bottom=0.12, top=0.92, left=0.05, right=0.95)
    cax = fig.add_axes([0.2, 0.08, 0.6, 0.025])
    
    if vmax is None:
        vmax = int(hexbin.get_array().max())
    ticks = np.linspace(vmin, vmax, 6)
    cbar = fig.colorbar(hexbin, cax=cax, orientation='horizontal', 
                       label=cbar_label, ticks=ticks)
    cbar.ax.tick_params(labelsize=9)

    # Title
    plot_title = f'{title} {statistic_value}'
    if aggregation != 'mean':
        plot_title += f' ({aggregation})'
    ax.set_title(plot_title, fontsize=13, pad=10)

    if save:
        if out_dir is None:
            raise ValueError("out_dir must be provided when save=True")
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / f"mfp_gwp_geographic_hexbin_EUROPE_{statistic_value}_{aggregation}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')

    plt.close()

    # Statistics
    print(f"Statistik für {statistic_value} (Aggregation: {aggregation}):")
    if aggregation == 'count':
        print(f"Maximale Anzahl von Punkten in einem Hexagon: {hexbin.get_array().max()}")
        print(f"Gesamtzahl der Hexagone: {len(hexbin.get_array())}")
    else:
        print(f"Minimum: {df[statistic_value].min():.4f}")
        print(f"Maximum: {df[statistic_value].max():.4f}")
        print(f"Mittelwert: {df[statistic_value].mean():.4f}")
        print(f"Anzahl der Datenpunkte: {len(df)}")
# def geographic_world_hexbin(df, statistic_value, title, aggregation='mean', gridsize=30, save=False, out_dir=None):
#     '''
#     Erstellt eine Weltkarte mit Hexbin-Darstellung statistischer Werte
    
#     Parameter:
#     ----------
#     df : DataFrame
#         DataFrame mit den geografischen Daten und statistischen Werten
#     statistic_value : str
#         Spaltenname des zu visualisierenden statistischen Werts
#     aggregation : str, default='mean'
#         Aggregationsmethode für Werte innerhalb eines Hexagons:
#         'mean': Mittelwert (Standard)
#         'max': Maximum
#         'min': Minimum
#         'count': Anzahl der Punkte
#     gridsize : int, default=30
#         Anzahl der Hexagone in x-Richtung
#     save : bool, default=False
#         Ob die Grafik gespeichert werden soll
#     out_dir : Path, default=None
#         Pfad zum Speicherverzeichnis
#     '''
#     import matplotlib.pyplot as plt
#     import cartopy.crs as ccrs
#     import cartopy.feature as cfeature
#     import numpy as np
#     import math

#     # Gültige Aggregationsmethoden
#     valid_aggregations = ['mean', 'max', 'min', 'count', 'median']
#     if aggregation not in valid_aggregations:
#         raise ValueError(f"Aggregation must be one of {valid_aggregations}")

#     # Farblogik für Statistikwerte
#     stat_config = {
#         "R2": {"cmap": "viridis", "vmin": 0, "vmax": 1, "label": r"$R^2$ (1 = gut, 0 = schlecht)"},
#         "spearman_cor": {"cmap": "coolwarm", "vmin": -1, "vmax": 1, "label": r"Spearman $\rho$ (-1..1)"},
#         "MAE": {"cmap": "viridis_r", "label": "MAE (0 = gut, hoch = schlecht)"},
#         "RMSE": {"cmap": "viridis_r", "label": "RMSE (0 = gut, hoch = schlecht)"},
#     }

#     # Standard min/max
#     if aggregation == 'count':
#         vmax = None
#         vmin = 0
#     else:
#         data_min = df[statistic_value].min()
#         data_max = df[statistic_value].max()
#         vmin, vmax = data_min, data_max

#     # Basismap erstellen
#     fig = plt.figure(figsize=(16, 8), dpi=150)
#     ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson())

#     ax.add_feature(cfeature.COASTLINE.with_scale('50m'))
#     ax.add_feature(cfeature.BORDERS.with_scale('50m'), linestyle=':')
#     ax.add_feature(cfeature.LAND.with_scale('50m'), alpha=0.1)
#     ax.add_feature(cfeature.OCEAN.with_scale('50m'), alpha=0.1)
#     ax.set_global()

#     # Colormap setzen
#     base_cmap = 'coolwarm'
#     if statistic_value in stat_config:
#         cfg = stat_config[statistic_value]
#         cmap = cfg.get("cmap", base_cmap)
#         vmin = cfg.get("vmin", vmin)
#         vmax = cfg.get("vmax", vmax)
#         cbar_label = cfg.get("label", statistic_value)
#     else:
#         cmap = base_cmap
#         cbar_label = statistic_value

#     # Aggregationsfunktion
#     if aggregation == 'mean':
#         reduce_C_function = np.mean
#     elif aggregation == 'median':
#         reduce_C_function = np.median
#     elif aggregation == 'max':
#         reduce_C_function = np.max
#     elif aggregation == 'min':
#         reduce_C_function = np.min
#     elif aggregation == 'count':
#         reduce_C_function = len

#     # Hexbin
#     hexbin = ax.hexbin(
#         df['latitude'], df['longitude'],
#         C=df[statistic_value] if aggregation != 'count' else None,
#         gridsize=gridsize,
#         reduce_C_function=reduce_C_function,
#         cmap=cmap,
#         alpha=0.7,
#         linewidths=0.4,
#         edgecolors='darkgrey',
#         transform=ccrs.PlateCarree(),
#         vmin=vmin,
#         vmax=vmax
#     )

#     # Colorbar
#     plt.subplots_adjust(bottom=0.15)
#     cax = fig.add_axes([0.15, 0.08, 0.7, 0.03])

#     if vmax is None:
#         vmax = int(hexbin.get_array().max())
#     ticks = np.linspace(vmin, vmax, 6)

#     cbar = fig.colorbar(hexbin, cax=cax, orientation='horizontal',
#                         label=cbar_label, ticks=ticks)
#     cbar.ax.tick_params(labelsize=10)

#     # Titel
#     title = f'{title} {statistic_value}'
#     if aggregation != 'mean':
#         title += f' ({aggregation})'
#     ax.set_title(title, fontsize=14)

#     # Save
#     if save:
#         if out_dir is None:
#             raise ValueError("out_dir must be provided when save=True")
#         out_dir = Path(out_dir)
#         out_dir.mkdir(parents=True, exist_ok=True)
#         output_path = out_dir / f"mfp_gwp_geographic_hexbin_{statistic_value}_{aggregation}.png"
#         plt.savefig(output_path, dpi=300, bbox_inches='tight')

#     plt.close()


#     # Statistik-Output
#     print(f"Statistik für {statistic_value} (Aggregation: {aggregation}):")
#     if aggregation == 'count':
#         print(f"Maximale Anzahl von Punkten in einem Hexagon: {hexbin.get_array().max()}")
#         print(f"Gesamtzahl der Hexagone: {len(hexbin.get_array())}")
#     else:
#         print(f"Minimum: {df[statistic_value].min()}")
#         print(f"Maximum: {df[statistic_value].max()}")
#         print(f"Mittelwert: {df[statistic_value].mean()}")
#         print(f"Anzahl der Datenpunkte: {len(df)}")


# def geographic_europe_hexbin(df, statistic_value, title, aggregation='mean', gridsize=30, save=False, out_dir=None):
#     """
#     Erstellt eine Europakarte mit Hexbin-Darstellung statistischer Werte.
#     Gleiche Logik wie geographic_world_hexbin, aber mit Fokus auf Europa.
#     """
#     import matplotlib.pyplot as plt
#     import cartopy.crs as ccrs
#     import cartopy.feature as cfeature
#     import numpy as np
#     import math

#     # gleiche Aggregationslogik wie in deiner world-Funktion
#     valid_aggregations = ['mean', 'max', 'min', 'count', 'median']
#     if aggregation not in valid_aggregations:
#         raise ValueError(f"Aggregation must be one of {valid_aggregations}")

#     # coerce save if passed as string ("True" from your script)
#     if isinstance(save, str):
#         save = save.lower() in ('true', '1', 'yes')

#     # If statistic not present (and not doing a count), skip plotting
#     if aggregation != 'count' and statistic_value not in df.columns:
#         print(f"Statistic '{statistic_value}' not found in dataframe columns: {df.columns.tolist()}. Skipping plot.")
#         return None

#     # tolerate Latitude/longitude capitalization variants
#     lat_col = 'latitude' if 'latitude' in df.columns else ('Latitude' if 'Latitude' in df.columns else None)
#     lon_col = 'longitude' if 'longitude' in df.columns else ('Longitude' if 'Longitude' in df.columns else None)
#     if lat_col is None or lon_col is None:
#         print("Latitude/Longitude columns not found. Skipping plot.")
#         return None

#     # Farblogik für bestimmte Statistikwerte
#     stat_config = {
#         "R2": {"cmap": "viridis", "vmin": 0, "vmax": 1, "label": r"$R^2$ (1 = gut, 0 = schlecht)"},
#         "spearman_cor": {"cmap": "coolwarm", "vmin": -1, "vmax": 1, "label": r"Spearman $\rho$ (-1..1)"},
#         "MAE": {"cmap": "viridis_r", "label": "MAE (0 = gut, hoch = schlecht)"},
#         "RMSE": {"cmap": "viridis_r", "label": "RMSE (0 = gut, hoch = schlecht)"},
#     }

#     # Dynamische min/max
#     if aggregation == 'count':
#         vmax = None
#         vmin = 0
#     else:
#         data_min = df[statistic_value].min()
#         data_max = df[statistic_value].max()
#         vmin, vmax = data_min, data_max

#     # Setup Karte für Europa
#     fig = plt.figure(figsize=(10, 8), dpi=150)
#     ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    
#     ax.add_feature(cfeature.COASTLINE.with_scale('50m'))
#     ax.add_feature(cfeature.BORDERS.with_scale('50m'), linestyle=':')
#     ax.add_feature(cfeature.LAND.with_scale('50m'), alpha=0.1)
#     ax.add_feature(cfeature.OCEAN.with_scale('50m'), alpha=0.1)

#     # Europa-Auschnitt (Longitude: -25 bis 45, Latitude: 34 bis 72)
#     ax.set_extent([-25, 44, 36, 69], crs=ccrs.PlateCarree())

#     # Colormap auswählen
#     base_cmap = 'coolwarm'
#     if statistic_value in stat_config:
#         cfg = stat_config[statistic_value]
#         cmap = cfg.get("cmap", base_cmap)
#         vmin = cfg.get("vmin", vmin)
#         vmax = cfg.get("vmax", vmax)
#         cbar_label = cfg.get("label", statistic_value)
#     else:
#         cmap = base_cmap
#         cbar_label = statistic_value

#     # Aggregation
#     if aggregation == 'mean':
#         reduce_C_function = np.mean
#     elif aggregation == 'median':
#         reduce_C_function = np.median
#     elif aggregation == 'max':
#         reduce_C_function = np.max
#     elif aggregation == 'min':
#         reduce_C_function = np.min
#     elif aggregation == 'count':
#         reduce_C_function = len

#     # Hexbin
#     hexbin = ax.hexbin(
#         df[lat_col], df[lon_col],
#         C=df[statistic_value] if aggregation != 'count' else None,
#         gridsize=gridsize,
#         reduce_C_function=reduce_C_function,
#         cmap=cmap,
#         alpha=0.7,
#         linewidths=0.4,
#         edgecolors='darkgrey',
#         transform=ccrs.PlateCarree(),
#         vmin=vmin,
#         vmax=vmax
#     )

#     # Colorbar
#     cax = fig.add_axes([0.15, 0.08, 0.7, 0.03])
#     if vmax is None:
#         vmax = int(hexbin.get_array().max())
#     ticks = np.linspace(vmin, vmax, 6)
#     cbar = fig.colorbar(hexbin, cax=cax, orientation='horizontal', label=cbar_label, ticks=ticks)
#     cbar.ax.tick_params(labelsize=10)

#     # Titel
#     title = f'{title} {statistic_value}'
#     if aggregation != 'mean':
#         title += f' ({aggregation})'
#     ax.set_title(title, fontsize=14)

#     if save:
#         if out_dir is None:
#             raise ValueError("out_dir must be provided when save=True")
#         out_dir = Path(out_dir)
#         out_dir.mkdir(parents=True, exist_ok=True)
#         output_path = out_dir / f"mfp_gwp_geographic_hexbin_EUROPE_{statistic_value}_{aggregation}.png"
#         plt.savefig(output_path, dpi=300, bbox_inches='tight')

#     plt.close()

#     # Statistik-Output
#     print(f"Statistik für {statistic_value} (Aggregation: {aggregation}):")
#     if aggregation == 'count':
#         print(f"Maximale Anzahl von Punkten in einem Hexagon: {hexbin.get_array().max()}")
#         print(f"Gesamtzahl der Hexagone: {len(hexbin.get_array())}")
#     else:
#         print(f"Minimum: {df[statistic_value].min()}")
#         print(f"Maximum: {df[statistic_value].max()}")
#         print(f"Mittelwert: {df[statistic_value].mean()}")
#         print(f"Anzahl der Datenpunkte: {len(df)}")


import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from highlight_text import ax_text


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


# Convenience-Funktionen für häufige Fälle 
def plot_two_lakes(df1, title1, df2, title2): 
    quick_monthly_plot((df1, title1), (df2, title2)) 
def plot_three_lakes(df1, title1, df2, title2, df3, title3): 
    quick_monthly_plot((df1, title1), (df2, title2), (df3, title3)) 
def plot_four_lakes(df1, title1, df2, title2, df3, title3, df4, title4): 
    quick_monthly_plot((df1, title1), (df2, title2), (df3, title3), (df4, title4)) 
def plot_5_lakes(df1, title1, df2, title2, df3, title3, df4, title4, df5, title5): 
    quick_monthly_plot((df1, title1), (df2, title2), (df3, title3), (df4, title4), (df5, title5))