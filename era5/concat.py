import xarray as xr
import glob
import re
import pandas as pd

# Get a sorted list of all files.
files = sorted(glob.glob("ERA5_temps_*.nc"))

datasets = []

for file in files:
    # Open the dataset.
    ds = xr.open_dataset(file)
    
    # Extract year and month from the filename.
    m = re.search(r"ERA5_temps_(\d{4})_(\d{2})\.nc", file)
    if m:
        file_year = int(m.group(1))
        file_month = int(m.group(2))
    else:
        raise ValueError(f"File name {file} does not match the expected pattern.")
    
    # Convert the last time coordinate to a pandas timestamp.
    last_time = pd.to_datetime(ds['time'][-1].values)
    
    # Check if the last time step belongs to the next month.
    if last_time.month != file_month:
        # Drop the last time step.
        ds = ds.isel(time=slice(0, -1))
    
    datasets.append(ds)

# Concatenate all datasets along the time dimension.
combined = xr.concat(datasets, dim='time')
combined = combined.sortby('time')  # Ensure the data is sequential by date.

# Write the combined dataset to a new netCDF file.
combined.to_netcdf("combined_ERA5.nc")
