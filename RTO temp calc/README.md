# Balancing Authority Population-Weighted Temperature Analysis

This script calculates population-weighted temperature for each balancing authority in the United States using ERA5 temperature data and population density data.

## Requirements

Install the required dependencies with:

```bash
pip install -r ba_temp_requirements.txt
```

## Data Sources

The script uses the following data:
1. ERA5 temperature data - `/Users/adessler/Documents/CopyFolder/national energy-temp analysis/era5/combined_ERA5.nc`
2. Population density data - `/Users/adessler/Documents/CopyFolder/national energy-temp analysis/gpw_v4_population_density_rev11_2020_2pt5_min.tif`
3. Balancing Authorities shapefile - `/Users/adessler/Documents/CopyFolder/national energy-temp analysis/RTO temp calc/Balancing_Authorities/Balancing_Authorities.shp`

## How It Works

The script:
1. Loads the balancing authorities shapefile
2. Loads population density data
3. Loads ERA5 temperature data
4. For each balancing authority:
   - Clips the temperature data to the balancing authority boundary
   - Interpolates population data to match the ERA5 grid
   - Calculates population-weighted temperature (with cosine latitude adjustment)
   - Saves individual results to NetCDF files
5. Combines all results into a single NetCDF file

## Running the Script

Simply run:

```bash
python balancing_authority_temp.py
```

## Output

The script creates a `weighted_temps` directory with:
- Individual NetCDF files for each balancing authority named `{BA_NAME}_weighted_temp.nc`
- A combined file with all results: `all_ba_weighted_temps.nc`

## Methodology

The population weighting methodology follows these steps:
1. Temperature data is clipped to each balancing authority boundary
2. Population density is interpolated to match the temperature grid
3. Weights are calculated as: population * cos(latitude)
4. A weighted average is calculated across all grid cells in the balancing authority

If no population data is available for a balancing authority, the script falls back to geographic weighting (cos(latitude)) only.

## Troubleshooting

If you encounter issues with missing data or empty results:
- Check that the ERA5 data covers the balancing authority region
- Verify that the population density data is properly loaded
- Ensure the coordinate reference systems match between datasets 