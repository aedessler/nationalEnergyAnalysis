import fiona
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape, MultiPolygon
import pyproj

def calculate_region_centroids(shapefile_path):
    # Extract region names and geometries using Fiona
    region_names = []
    geometries = []

    with fiona.open(shapefile_path, "r") as src:
        for feature in src:
            region_names.append(feature["properties"].get("NAME", "Unknown"))
            geom = shape(feature["geometry"])
            if isinstance(geom, MultiPolygon):
                geom = max(geom.geoms, key=lambda p: p.area)  # Take the largest polygon
            geometries.append(geom)

    # Convert to a GeoDataFrame
    gdf = gpd.GeoDataFrame(geometry=geometries, crs="EPSG:3857")

    # Calculate centroids
    gdf["centroid_x"] = gdf.geometry.centroid.x
    gdf["centroid_y"] = gdf.geometry.centroid.y

    # Convert to latitude and longitude
    transformer = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    gdf["longitude"], gdf["latitude"] = transformer.transform(gdf["centroid_x"].values, gdf["centroid_y"].values)

    # Create DataFrame with region names as index
    centroids_df = pd.DataFrame({"name": region_names, "latitude": gdf["latitude"], "longitude": gdf["longitude"]}).set_index("name")

    return centroids_df

# Example usage:
# shapefile_path = "path/to/your/shapefile.shp"
# centroids_df = calculate_region_centroids(shapefile_path)
# centroids_df.to_csv("region_centroids.csv")
