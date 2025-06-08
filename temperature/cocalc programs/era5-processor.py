#!/usr/bin/env python
# coding: utf-8

import xarray as xr
import pandas as pd
import numpy as np
import os
import time
import sys
import gc
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Check command line arguments
if len(sys.argv) != 2:
    print("Usage: python era5-processor.py <year>")
    print("Example: python era5-processor.py 1979")
    sys.exit(1)

try:
    year = int(sys.argv[1])
    print(f"Processing year: {year}")
except ValueError:
    print(f"Error: Year must be an integer. You provided: {sys.argv[1]}")
    sys.exit(1)

# Start timing the whole process
start_time = time.time()

# Create output directory if it doesn't exist
# os.makedirs("data", exist_ok=True)

# Check if the output file already exists
output_file = f"/data/ERA5_temps_{year}.nc"
if os.path.exists(output_file):
    print(f"Year {year} already processed (file {output_file} exists). Skipping.")
    sys.exit(0)

# Create a directory for intermediate results if it doesn't exist
os.makedirs("/data/intermediate", exist_ok=True)

# Process each month separately
monthly_datasets = []

for month in range(1, 13):
    month_start_time = time.time()
    
    # Define the month timeframe
    if month == 12:
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year+1}-01-01"
    else:
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month+1:02d}-01"
    
    # Set up intermediate file path
    month_file = f"/data/intermediate/ERA5_temps_{year}_{month:02d}.nc"
    
    # Check if month file already exists
    if os.path.exists(month_file):
        print(f"Month {month:02d} already processed, loading from file.")
        # month_data = xr.open_dataset(month_file)['2m_temperature']
        # monthly_datasets.append(month_data)
        continue
    
    print(f"Processing month {month:02d} for year {year}")
    print(f"Loading ERA5 data for {start_date} to {end_date}")
    
    try:
        # Load ERA5 data for this month
        dataset = xr.open_zarr(
            'gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3',
            storage_options={'token': 'anon'},
            consolidated=True
        )

        # Select the month we need
        temp_data = dataset['2m_temperature'].sel(time=slice(start_date, end_date))
        temp_data = temp_data - 273.15  # Convert Kelvin to Celsius

        # Compute the daily mean temperature
        temp_data = temp_data.resample(time='D').mean()

        # Convert longitude from 0-360 to -180 to 180
        temp_data = temp_data.assign_coords({
            "longitude": (((temp_data.longitude + 180) % 360) - 180)
        })

        # Sort by coordinates and subset to North America region
        temp_data = temp_data.sortby("longitude")
        temp_data = temp_data.sortby("latitude")
        temp_data = temp_data.sel(latitude=slice(24, 55), longitude=slice(-125, -66))
        temp_data.load()
        
        # Save month data
        temp_data.to_netcdf(month_file)

        # Add to our list
        # monthly_datasets.append(temp_data)
        
        # Clean up memory
        del dataset
        gc.collect()
        
        month_end_time = time.time()
        print(f"Month {month:02d} processed in {month_end_time - month_start_time:.2f} seconds")
        
    except Exception as e:
        print(f"Error processing month {month:02d}: {str(e)}")
        # Continue with next month

        
# Combine all months and save the yearly file
if monthly_datasets and False:
    print(f"Combining all months for year {year}...")
    yearly_data = xr.concat(monthly_datasets, dim="time")
    
    # Save the yearly file
    print(f"Saving year {year} results to {output_file}")
    yearly_data.to_netcdf(output_file)
    
    # Optional: clean up intermediate files
    for month in range(1, 13):
        month_file = f"data/intermediate/ERA5_temps_{year}_{month:02d}.nc"
        if os.path.exists(month_file):
            try:
                os.remove(month_file)
                print(f"Removed intermediate file: {month_file}")
            except Exception as e:
                print(f"Could not remove {month_file}: {str(e)}")
# else:
#     print(f"No valid monthly data for year {year}")

end_time = time.time()
print(f"Year {year} processed in {end_time - start_time:.2f} seconds")