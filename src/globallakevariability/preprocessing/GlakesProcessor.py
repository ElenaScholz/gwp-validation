from pathlib import Path
import geopandas as gpd
import pandas as pd
import os
import gc

class GLAKESProcessor:
    def __init__(self,
                 root_to_GLAKES_folder: str,
                 path_to_hylak_dataset: str,
                 gwp_dataset_with_hylak_ids # # dataframe that contains only the hylak ids and corresponding names of statistical gwp data
                 ):
        self.GLAKES_files = [Path(root_to_GLAKES_folder) / file for file in os.listdir(Path(root_to_GLAKES_folder))]
        self.hylak_dataset = gpd.read_file(Path(path_to_hylak_dataset))
        self.gwp_with_hylak_id = gwp_dataset_with_hylak_ids
        self.gwp_glakes_dict = {}

        #self.GLAKES_geometries = {}


    def prepare_GLAKES_geometries(self):
        print("Preparing GLAKES geometries...")
        shp_files = [file for file in self.GLAKES_files if str(file).endswith(".shp")]
        if not shp_files:
            return None
        glakes_shp = gpd.GeoDataFrame(
            pd.concat([gpd.read_file(shp) for shp in shp_files], ignore_index=True),
            crs="EPSG:4326"
        )
        glakes_subset = glakes_shp[["Lake_id", "Area_bound", "geometry"]].copy()

        glakes_subset = glakes_subset.rename(columns={"Lake_id": "GLAKES_id", "Area_bound": "GLAKES_area"})
        glakes_subset = glakes_subset[glakes_subset["GLAKES_area"] > 20]
        return glakes_subset
    
    def prepare_Hydrolakes_geometries(self):
        print("Preparing HydroLAKES geometries...")
        hylak_subset = self.hylak_dataset[["Hylak_id", "Lake_area", "geometry"]].copy()
        hylak_subset = hylak_subset.rename(columns={"Lake_area": "Hylak_area"})
        hylak_subset = hylak_subset[hylak_subset["Hylak_area"] > 20]
        return hylak_subset
    
    @staticmethod
    def match_glakes_and_hylak(glakes_shp, hydrolakes_shp, threshold_percentage=10):
        # Ensure both GeoDataFrames use the same CRS
        glakes_shp = glakes_shp.to_crs("EPSG:3857")
        hydrolakes_shp = hydrolakes_shp.to_crs("EPSG:3857")

        overlapping_lakes = gpd.sjoin(
            glakes_shp, 
            hydrolakes_shp, 
            how="inner", 
            predicate="intersects",
            rsuffix='hydro'  # This will rename the right geometry to geometry_hydro
        )
        # Show the number of overlapping lakes
        print(f"Number of overlapping lakes: {len(overlapping_lakes)}")

        # Add the hydrolakes geometry by merging with the original hydrolakes GeoDataFrame
        overlapping_lakes = overlapping_lakes.merge(
            hydrolakes_shp[['geometry']].rename(columns={'geometry': 'geometry_hydro'}),
            left_on='index_hydro',
            right_index=True,
            how='left'
        )

        overlapping_lakes.rename(columns = {"GLAKES_area":"glakes_area" }, inplace=True)

        # Calculate intersection area and filter for >= x% overlap
        overlapping_lakes['intersection_area'] = overlapping_lakes.geometry.intersection(
            overlapping_lakes['geometry_hydro']
        ).area

        # Use the original glakes_area instead of recalculating it
        overlapping_lakes['intersection_pct'] = (
            overlapping_lakes['intersection_area'] / overlapping_lakes['glakes_area'] * 100
        )

        # Keep only rows with >= x% intersection
        overlapping_lakes_pct = overlapping_lakes[overlapping_lakes['intersection_pct'] >= threshold_percentage]

        print(f"Total overlaps: {len(overlapping_lakes)}")
        print(f"Overlaps with >= {threshold_percentage}: {len(overlapping_lakes_pct)}")

        return overlapping_lakes_pct