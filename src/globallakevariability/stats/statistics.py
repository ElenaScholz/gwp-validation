import numpy as np
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error
import pandas as pd
from statistics import mean, stdev, variance
from functools import reduce
from scipy import stats

def correlation(x, y, method='spearman'):
    """Calculate correlation between two series."""
    if method == 'pearson':
        return stats.pearsonr(x, y)[0]
    elif method == 'spearman':
        return stats.spearmanr(x, y)[0]
    else:
        raise ValueError(f"Unknown correlation method: {method}")


def calculate_stats_per_lake(lakes_dict, gwp_column, validation_column, number_of_samples, use_zscore=False, correlation_method='spearman'):
    stats_list = []
    sample_dfs = {}
    constant_array_lakes = []
    
    for lake_id, lake_df in lakes_dict.items():
        sample_size = min(number_of_samples, len(lake_df))
        if sample_size == 0:
            print(f"Lake {lake_id} has no data points, skipping...")
            continue
            
        sample_df = lake_df.sample(n=sample_size, random_state=1)
        sample_df = sample_df.dropna(subset=[validation_column, gwp_column])

        sample_dfs[lake_id] = sample_df

        if sample_df.empty:
            continue

        gwp_vals = sample_df[gwp_column]
        val_vals = sample_df[validation_column]

        # Safely get lake metadata
        latitude = sample_df['Latitude'].iloc[0] if 'Latitude' in sample_df.columns else None
        longitude = sample_df['Longitude'].iloc[0] if 'Longitude' in sample_df.columns else None
        hylak_id = sample_df['Hylak_id'].iloc[0] if 'Hylak_id' in sample_df.columns else None
        glakes_id = sample_df['GLAKES_id'].iloc[0] if 'GLAKES_id' in sample_df.columns else None

        val_is_constant = len(set(val_vals)) <= 1
        gwp_is_constant = len(set(gwp_vals)) <= 1

        if val_is_constant or gwp_is_constant:
            constant_array_lakes.append({
                'hylak_id': hylak_id,
                'glakes_id': glakes_id,
                'lake_id': lake_id,
                'gwp_is_constant': gwp_is_constant,
                'val_is_constant': val_is_constant
            })

        if not val_is_constant and not gwp_is_constant and len(val_vals) > 1:
            try:
                spearman_R = correlation(val_vals, gwp_vals, method=correlation_method)
                stats_values = {
                    'Hylak_id': hylak_id,
                    'GLAKES_id': glakes_id,
                    'latitude': latitude,
                    'longitude': longitude,
                    f'gwp_mean{"_z" if use_zscore else ""}': mean(gwp_vals),
                    f'val_mean{"_z" if use_zscore else ""}': mean(val_vals),
                    f'gwp_stdev{"_z" if use_zscore else ""}': stdev(gwp_vals),
                    f'val_stdev{"_z" if use_zscore else ""}': stdev(val_vals),
                    f'gwp_var{"_z" if use_zscore else ""}': variance(gwp_vals),
                    f'val_var{"_z" if use_zscore else ""}': variance(val_vals),
                    'spearman_cor': spearman_R,
                    "R2": spearman_R * spearman_R,
                    'RMSE': np.sqrt(mean_squared_error(val_vals, gwp_vals)),
                    'MAE': mean_absolute_error(val_vals, gwp_vals)
                }
                stats_list.append(stats_values)
            except Exception as e:
                print(f"Error calculating statistics for lake {lake_id}: {e}")

    stats_df = pd.DataFrame(stats_list)

    # Only try to access/drop GLAKES_id if the column exists
    if 'GLAKES_id' in stats_df.columns:
        if stats_df[stats_df['GLAKES_id'].notna()].empty:
            stats_df = stats_df.drop(columns=['GLAKES_id'])
    return sample_dfs, constant_array_lakes, stats_df


def analyze_lakes_by_month(lakes_dict, min_data_points=1):
    """
    Performs all analyses for lakes on a monthly basis.
    
    Parameters:
    lakes_dict: Dictionary with Lake_ID as key and corresponding DataFrame as value
    
    Returns:
    Dictionary with all analysis results
    """
    results = {}
    
    try:
        # Calculate monthly statistics
        print("Calculating monthly statistics...")
        monthly_stats_df, constant_array_lakes = calculate_monthly_stats_relaxed(lakes_dict, min_data_points=min_data_points)
        results['monthly_statistics'] = monthly_stats_df
        results['constant_lakes'] = constant_array_lakes
        
        # Create monthly time series
        print("Creating monthly time series...")
        monthly_time_series = create_monthly_time_series(lakes_dict)
        results['monthly_time_series'] = monthly_time_series
        
        # Only analyze seasonal patterns if we have valid monthly statistics
        if not monthly_stats_df.empty:
            print("Analyzing seasonal patterns...")
            seasonal_patterns = analyze_lake_variations(monthly_stats_df)
            results['seasonal_patterns'] = seasonal_patterns
        else:
            print("Skipping seasonal pattern analysis due to empty monthly statistics.")
            results['seasonal_patterns'] = pd.DataFrame()
            
        return results
    except Exception as e:
        print(f"Error in analyze_lakes_by_month: {e}")
        return results