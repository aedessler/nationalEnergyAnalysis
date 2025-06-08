#!/usr/bin/env python
# coding: utf-8

import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import xarray as xr
import rioxarray
import rasterio
import os
import pandas as pd
from tqdm import tqdm

# Set paths to data files
ERA5_FILE = '/Users/adessler/Documents/CopyFolder/national energy-temp analysis/era5/combined_ERA5.nc'
POPULATION_FILE = '/Users/adessler/Documents/CopyFolder/national energy-temp analysis/RTO temp calc/gpw_v4_population_density_rev11_2020_2pt5_min.tif'
BALANCING_AUTHORITIES_FILE = '/Users/adessler/Documents/CopyFolder/national energy-temp analysis/RTO temp calc/Balancing_Authorities/Balancing_Authorities.shp'
OUTPUT_DIR = '/Users/adessler/Documents/CopyFolder/national energy-temp analysis/RTO temp calc/weighted_temps'

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load the balancing authorities shapefile
print("Loading balancing authorities shapefile...")
ba_gdf = gpd.read_file(BALANCING_AUTHORITIES_FILE)
print(f"Found {len(ba_gdf)} balancing authorities")

# Reproject the balancing authorities to EPSG:4326 (lat/lon) to match ERA5 data
print(f"Original CRS: {ba_gdf.crs}")
ba_gdf = ba_gdf.to_crs("EPSG:4326")
print(f"Reprojected CRS: {ba_gdf.crs}")

# Display the column names to identify the name/ID field
print("Balancing authority fields:", ba_gdf.columns.tolist())
ba_id_field = 'HIFLDname'  # Using the HIFLDname field instead of NAME since that field doesn't exist

# Load the population density data
print("Loading population density data...")
with rasterio.open(POPULATION_FILE) as src:
    pop_data = src.read()
    pop_meta = src.meta

# Create an xarray DataArray from the population data
pop_df = xr.DataArray(
    pop_data.squeeze(), 
    dims=('lat', 'lon'), 
    coords={
        'lat': pop_meta['transform'][5] + np.arange(pop_data.shape[1]) * pop_meta['transform'][4],
        'lon': pop_meta['transform'][2] + np.arange(pop_data.shape[2]) * pop_meta['transform'][0]
    }
)

# Add CRS attribute
pop_df.attrs['crs'] = pop_meta['crs']
population = pop_df.where(pop_df > 0, np.nan)

# Round coordinates to 3 decimal places
population['lat'] = np.round(population.lat, 3)
population['lon'] = np.round(population.lon, 3)

# Load the ERA5 temperature data
print("Loading ERA5 temperature data...")
era5_ds = xr.open_dataset(ERA5_FILE)
print(f"ERA5 data dimensions: {era5_ds.dims}")
print(f"ERA5 latitude range: {era5_ds.latitude.min().values} to {era5_ds.latitude.max().values}")
print(f"ERA5 longitude range: {era5_ds.longitude.min().values} to {era5_ds.longitude.max().values}")

# Rename the temperature variable if needed
if '2m_temperature' in era5_ds.variables:
    era5_ds = era5_ds.rename({'2m_temperature': 't2m'})

# Make sure we have the right coordinate names
if 'latitude' in era5_ds.coords and 'longitude' in era5_ds.coords:
    era5_ds = era5_ds.rename({'latitude': 'lat', 'longitude': 'lon'})

# Function to process a single balancing authority
def process_ba(ba_geom, ba_name):
    print(f"Processing {ba_name}...")
    print(f"BA bounds: {ba_geom.bounds}")
    
    # Convert the era5 dataset to use x,y coordinates for clipping
    ds_to_clip = era5_ds.copy()
    ds_to_clip = ds_to_clip.rename({'lon': 'x', 'lat': 'y'})
    
    # Set the CRS for the dataset
    ds_to_clip = ds_to_clip.rio.write_crs("EPSG:4326")
    
    # Create a GeoDataFrame with just this BA geometry
    ba_single_gdf = gpd.GeoDataFrame(geometry=[ba_geom], crs=ba_gdf.crs)
    
    # Clip the dataset to the BA boundary
    try:
        clipped_ds = ds_to_clip.rio.clip(ba_single_gdf.geometry)
        clipped_ds = clipped_ds.rename({'x': 'lon', 'y': 'lat'})
        
        # Check if we have data after clipping
        if clipped_ds.sizes['lat'] == 0 or clipped_ds.sizes['lon'] == 0:
            print(f"Warning: No data points found within {ba_name} boundary.")
            return None
        
        # Interpolate population data to match the ERA5 grid
        pop_interpolated = population.interp(lon=clipped_ds.lon, lat=clipped_ds.lat)
        
        # Calculate weights (population * cos(lat))
        weights = (pop_interpolated * np.cos(np.deg2rad(clipped_ds.lat))).fillna(0)
        
        # Check if we have any non-zero weights
        if np.all(weights == 0):
            print(f"Warning: All weights are zero for {ba_name}. Using geographic weighting only.")
            weights = np.cos(np.deg2rad(clipped_ds.lat)).fillna(0)
        
        # Create weighted xarray Dataset
        weighted_data = clipped_ds.weighted(weights)
        
        # Calculate the weighted mean along lat and lon dimensions
        weighted_mean = weighted_data.mean(dim=['lat', 'lon'])
        
        # Save the result to a NetCDF file
        output_file = os.path.join(OUTPUT_DIR, f"{ba_name.replace(' ', '_').replace('/', '_')}_weighted_temp.nc")
        weighted_mean.to_netcdf(output_file)
        
        print(f"Saved weighted temperature for {ba_name} to {output_file}")
        return weighted_mean
        
    except Exception as e:
        print(f"Error processing {ba_name}: {str(e)}")
        return None

# Process each balancing authority
results = {}
for idx, row in tqdm(ba_gdf.iterrows(), total=len(ba_gdf)):
    ba_name = row[ba_id_field]
    result = process_ba(row.geometry, ba_name)
    if result is not None:
        results[ba_name] = result

# Optional: Combine all results into a single dataset
if results:
    print("Combining all results...")
    combined_ds = xr.concat([ds.assign_coords(ba=name) for name, ds in results.items()], dim="ba")
    combined_ds.to_netcdf(os.path.join(OUTPUT_DIR, "all_ba_weighted_temps.nc"))
    print(f"Saved combined results to {os.path.join(OUTPUT_DIR, 'all_ba_weighted_temps.nc')}")
else:
    print("Warning: No results were generated for any balancing authority.")

print("Done!") 