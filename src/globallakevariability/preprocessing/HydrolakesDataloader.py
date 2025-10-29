import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, Point
from pathlib import Path
import re
from shapely import wkt

class HydroLakesGWP_DataLoading:

    """
        Loads and processes HydroLakes and Global Waterpack (GWP) datasets, optionally clipping to a 
        specific Area of Interest (AOI, Europe).

        This class handles:
            - Loading HydroLakes polygons
            - Loading GWP point data
            - Clipping datasets to Europe or ARLIE AOI
            - Performing spatial join between HydroLakes and GWP points
            - Saving processed outputs to disk

        Attributes:
            root (Path): Root directory of the project.
            save (bool): Whether to save processed outputs to disk.
            input_root (Path): Root folder for input datasets.
            input_gwp (Path): Path to GWP coordinate files.
            hydrolakes_path (Path): Path to HydroLakes shapefiles.
            output_root (Path): Root folder for outputs.
            output_arlie (Path): Output folder for ARLIE processed data.
            output_gwp (Path): Output folder for GWP processed data.
            output_hydrolakes (Path): Output folder for HydroLakes processed data.
            clip_to_arlie (bool): Whether to clip datasets to Europe/ARLIE AOI.
            aoi_gdf (GeoDataFrame): Polygon defining the AOI in Europe (EPSG:4326).
    """

    def __init__(self, root_dir: str = r"T:\DLR", clip_to_arlie: bool = False, save = True):
        """
        Initializes file paths, output folders, and AOI polygon.

        Args:
            root_dir (str): Root directory of project data. Defaults to r"T:\DLR".
            clip_to_arlie (bool): Whether to clip data to Europe/ARLIE area. Defaults to False.
            save (bool): Whether to save processed outputs. Defaults to True.
        """

        self.root = Path(root_dir)
        self.save = save  # Add this line to define self.save
        
        # Input-Pfade
        
        self.input_root = self.root / "Input"

        self.input_gwp = self.input_root / "GWP" / "00_coordinates_8247"  # This is your GWP path

        self.hydrolakes_path = self.input_root / "HydroLAKES_polys_v10" / "HydroLAKES_polys_v10_shp"

        # Output-Pfade
        self.output_root = self.root / "Output"
        self.output_arlie = self.output_root / "ARLIE"
        self.output_gwp = self.output_root / "GWP"
        self.output_hydrolakes = self.output_root / "Hydrolakes"

        # Falls Ordner noch nicht existieren, erstelle sie
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.output_arlie.mkdir(parents=True, exist_ok=True)
        self.output_gwp.mkdir(parents=True, exist_ok=True)
        self.output_hydrolakes.mkdir(parents=True, exist_ok=True)

        self.clip_to_arlie = clip_to_arlie
        
        # AOI-Polygon definieren (Europa in WGS84)
        self.west, self.east = -25.00, 44.00
        self.south, self.north = 36.00, 69.00

        wgs84_polygon = Polygon([
            (self.west, self.south), 
            (self.west, self.north), 
            (self.east, self.north), 
            (self.east, self.south), 
            (self.west, self.south)  # Polygon schließen
        ])

        self.aoi_gdf = gpd.GeoDataFrame({'geometry': [wgs84_polygon]}, crs="EPSG:4326")

    def load_hydrolakes(self):
        """
        Loads HydroLakes polygons, optionally clipping them to Europe/ARLIE AOI.

        Returns:
            GeoDataFrame: HydroLakes polygons (possibly clipped) with columns:
                'Hylak_id', 'Lake_name', 'Lake_area', 'Lake_type', 'geometry'.

        Notes:
            - Repairs invalid geometries using buffer(0).
            - Saves clipped dataset to disk if `self.save` is True.
        """
            
        if self.clip_to_arlie:
            output_file = self.output_hydrolakes / "hydrolakes_clipped_europe.gpkg"

            if output_file.exists():
                print("Geladene Hydrolakes aus:", output_file)
                return gpd.read_file(output_file)
            else: 
                # load hydrolakes 
                hydrolakes = gpd.read_file(self.hydrolakes_path / "HydroLAKES_polys_v10.shp")
                # create a subset with Information for further analysis 
                hydrolakes_europe = hydrolakes[['Hylak_id', 'Lake_name', 'Lake_area', "Lake_type", 'geometry']]

                print(hydrolakes_europe.is_valid.value_counts())
                hydrolakes_europe["geometry"] = hydrolakes_europe["geometry"].buffer(0)  # Repariere Geometrien

                hydrolakes_clipped = gpd.clip(hydrolakes_europe, self.aoi_gdf)
                print(f"The hydrolakes data set is clipped. There are {len(hydrolakes_clipped)} lakes within the given Arlie area")

                if self.save:
                    os.makedirs(self.output_hydrolakes, exist_ok=True)
                    hydrolakes_clipped.to_file(output_file, driver="GPKG")
                
                return hydrolakes_clipped
        else:
            # load hydrolakes polygon and save it as a variable
            hydrolakes = gpd.read_file(self.hydrolakes_path / "HydroLAKES_polys_v10.shp")
            return hydrolakes

    def load_gwp(self):
        """
        Loads Global Waterpack (GWP) point data, optionally clipping to Europe/ARLIE AOI.

        Returns:
            GeoDataFrame: GWP points with columns:
                'id', 'latitude', 'longitude', 'geometry'.

        Notes:
            - Reads all .txt files in the GWP input folder.
            - Skips files without content or wrong format.
            - Saves clipped dataset to disk if `self.save` is True.
        """

        def create_gwp_gdf():
            """Erstellt GeoDataFrame für GWP-Daten"""
            
            # load all gwp files containing the coordinates
            gwp_files = os.listdir(self.input_gwp)
            file_id, latitude, longitude = [], [], []

            for file in gwp_files:
                if not file.endswith('.txt'):  # Skip non-text files
                    continue
                    
                file_id.append(file[:-4])
                

                gwp_file_path = os.path.join(self.input_gwp, file)

                if os.path.exists(gwp_file_path):
                    with open(gwp_file_path, 'r') as f:
                        lines = f.readlines()

                    if len(lines) > 1:  # Check if file has content
                        for line in lines[1:]:  # Header-Zeile überspringen
                            if ";" in line:  # Ensure line has expected format
                                lat, lon = line.strip().split(";")
                                latitude.append(float(lat))
                                longitude.append(float(lon))

            # DataFrame erstellen
            if not file_id:  # Check if lists are empty
                return gpd.GeoDataFrame(columns=["id", "latitude", "longitude", "geometry"], crs="EPSG:4326") 
                
            gwp_df = pd.DataFrame({"id": file_id, "latitude": latitude, "longitude": longitude})
                               
            gwp_df["geometry"] = [Point(lat, lon) for lat, lon in zip(gwp_df["latitude"], gwp_df["longitude"])]
            gwp_gdf = gpd.GeoDataFrame(gwp_df, geometry="geometry", crs="EPSG:4326")
            print(f"In total there are {len(gwp_gdf)} GWP samples world wide")
            return gwp_gdf

        if self.clip_to_arlie:
            output_file = self.output_gwp / "gwp_clipped_europe.gpkg"

            if output_file.exists():
                print("Geladene Global Waterpack Daten aus:", output_file)
                return gpd.read_file(output_file)
            else:
                gwp_gdf = create_gwp_gdf()
                gwp_clipped = gpd.clip(gwp_gdf, self.aoi_gdf)
                if self.save:
                    os.makedirs(self.output_gwp, exist_ok=True)
                    gwp_clipped.to_file(output_file, driver="GPKG")
                return gwp_clipped
        else:
            gwp_gdf = create_gwp_gdf()
            print(f"There are {len(gwp_gdf)} GWP samples matching the AOI")
            return gwp_gdf
        
    def load_and_join_hydrolakes_gwp(self):
        """
        Loads HydroLakes and GWP datasets, clips them if required, and performs a spatial join.

        Returns:
            GeoDataFrame: GWP points including 'Hylak_id' from HydroLakes polygons.
        """
        
        # Lade HydroLakes-Daten
        hydrolakes_clipped = self.load_hydrolakes()
        
        # Lade GWP-Daten
        gwp_clipped = self.load_gwp()
        
        # Führe spatial join durch
        gwp_with_hylakID = gpd.sjoin(gwp_clipped, hydrolakes_clipped, how='left', predicate='within')
        
        gwp_with_hylakID = gwp_with_hylakID.drop(columns=['index_right'], errors='ignore')
        print(f"There are {len(gwp_with_hylakID)} gwp samples with a matching hydrolake for the further analysis")
        
        return gwp_with_hylakID