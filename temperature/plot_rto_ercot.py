import zipfile
import os
import geopandas as gpd
import fiona
import matplotlib.pyplot as plt
from shapely.geometry import shape, MultiPolygon, Polygon
import pyproj

# Define file paths
zip_file_path = "RTO_Regions.zip"
extract_dir = "RTO_Regions"

# Extract the zip file
with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

# Locate the shapefile
shapefile_path = os.path.join(extract_dir, "RTO_Regions", "RTO_Regions.shp")

# Projection transformer from EPSG:3857 to EPSG:4326
project = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

# Function to plot polygons with lat/lon axes
def plot_rto_regions():
    gdf = gpd.read_file(shapefile_path)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for _, row in gdf.iterrows():
        geom = row.geometry
        if isinstance(geom, MultiPolygon):
            for poly in geom.geoms:
                lon, lat = zip(*[project.transform(x, y) for x, y in poly.exterior.coords])
                ax.plot(lon, lat, color="black", alpha=0.6)
        else:
            lon, lat = zip(*[project.transform(x, y) for x, y in geom.exterior.coords])
            ax.plot(lon, lat, color="black", alpha=0.6)
    
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("RTO Regions Map (Lat/Lon Projection)")
    plt.show()

# Function to plot ERCOT load zones with different colors and labels
def plot_ercot_load_zones():
    ercot_gdf = []
    
    for feature in fiona.open(shapefile_path):
        if feature["properties"].get("RTO_ISO") == "ERCOT":
            geom = shape(feature["geometry"])
            zone_name = feature["properties"].get("LOC_NAME", "Unknown")
            if isinstance(geom, MultiPolygon):
                for poly in geom.geoms:
                    ercot_gdf.append((poly, zone_name))
            else:
                ercot_gdf.append((geom, zone_name))
    
    num_zones = len(ercot_gdf)
    colors = plt.cm.tab10.colors
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for i, (polygon, zone_name) in enumerate(ercot_gdf):
        lon, lat = zip(*[project.transform(x, y) for x, y in polygon.exterior.coords])
        ax.fill(lon, lat, color=colors[i % len(colors)], alpha=0.5, label=zone_name)
        
        centroid = polygon.centroid
        centroid_lon, centroid_lat = project.transform(centroid.x, centroid.y)
        ax.text(centroid_lon, centroid_lat, zone_name, fontsize=8, ha="center", va="center", color="black")

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("ERCOT Load Zones (Lat/Lon Projection)")

    handles, labels = ax.get_legend_handles_labels()
    unique_labels = dict(zip(labels, handles))
    ax.legend(unique_labels.values(), unique_labels.keys(), fontsize=8, loc="upper right")

    plt.show()

# Run the plots
if __name__ == "__main__":
    plot_rto_regions()
    plot_ercot_load_zones()
