import pandas as pd
import xarray as xr
import numpy as np
import json, sys
import warnings

# Filter out the FutureWarning about month end resampling
warnings.filterwarnings('ignore', category=FutureWarning, message="'M' is deprecated")

def generate_x(X, date):
    """Generate regressors for the regression of demand vs. temperature"""
    data = pd.DataFrame({
        'Temperature': X,
        'Temperature^2': X**2,
        'Temperature^3': X**3,
        'Temperature^4': X**4,
    }, index=date)

    # Make categorical variable for weekday vs. weekend
    data['category'] = (date.weekday < 5).astype(int)  # Weekday = 1, Weekend = 0
    
    # Add constant term
    data['Constant'] = 1

    return data

def predict_demand(X, dates, coefficients):
    """Predict demand using pre-computed polynomial coefficients"""
    data = generate_x(X, dates)
    
    # Calculate prediction using coefficients
    y_pred = (coefficients['constant'] +
              coefficients['temperature'] * data['Temperature'] +
              coefficients['temperature^2'] * data['Temperature^2'] +
              coefficients['temperature^3'] * data['Temperature^3'] +
              coefficients['temperature^4'] * data['Temperature^4'] +
              coefficients['weekday_effect'] * data['category'])
    
    return y_pred

def analyze_zone(zone_data, era5_ds, polynomial_fits):
    """Analyze temperature-demand relationship for a single zone using pre-computed fits"""
    print(f"\nAnalyzing zone: {zone_data['centroid name']}")
    
    # Get zone coordinates
    zone_lat = zone_data['latitude']
    zone_lon = zone_data['longitude']
    print(f"Zone coordinates: lat={zone_lat}, lon={zone_lon}")
    
    # Find the matching polynomial fit
    zone_fit = None
    for fit in polynomial_fits['fits']:
        if fit['zone_name'] == zone_data['centroid name']:
            zone_fit = fit
            break
    
    if zone_fit is None:
        raise ValueError(f"No polynomial fit found for zone {zone_data['centroid name']}")
    
    # Extract temperature for nearest point
    temp_data = era5_ds['2m_temperature'].sel(
        latitude=zone_lat,
        longitude=zone_lon,
        method='nearest'
    )
    
    print(f"Weekday Effect: {zone_fit['coefficients']['weekday_effect']:.2f} GW")
    
    # Function to predict demand for a given time period
    def predict_period_demand(start_year, end_year):
        print(f"\nPredicting demand for period {start_year}-{end_year}")
        
        # Get temperature data for the period
        period_temp = temp_data.sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))
        if len(period_temp) == 0:
            raise ValueError(f"No temperature data found for period {start_year}-{end_year}")
            
        daily_period_temp = period_temp.resample(time='D').mean()
        
        # Get dates for the period
        dates = daily_period_temp.time.to_index()
        
        # Get predictions using pre-computed coefficients
        predictions = predict_demand(daily_period_temp.values, dates, zone_fit['coefficients'])
        
        # Create series with datetime index
        pred_series = pd.Series(predictions, index=dates)
        
        # Calculate monthly averages
        monthly_means = pred_series.resample('ME').mean()

        # Group by month and calculate mean across years
        monthly_results = monthly_means.groupby(monthly_means.index.month).mean()
        
        return monthly_results
    
    # Calculate average demand for both periods
    try:
        demand_1951_1980 = predict_period_demand(1951, 1980)
        demand_2015_2024 = predict_period_demand(2015, 2024)
    except Exception as e:
        print(f"Error predicting demand: {str(e)}")
        raise
    
    # Calculate changes
    changes = demand_2015_2024 - demand_1951_1980
    print("\nAnalysis complete for this zone")
    
    return changes, demand_1951_1980, demand_2015_2024

print("Starting analysis...")

# Read mapping file
try:
    mapping_df = pd.read_csv('mapping.csv')
    print(f"Found {len(mapping_df)} total zones in mapping file")
except Exception as e:
    print(f"Error reading mapping.csv: {str(e)}")
    sys.exit()

# Read centroids file
try:
    centroids_df = pd.read_csv('temperature/region_centroids.csv')
    print(f"Found {len(centroids_df)} zones in centroids file")
except Exception as e:
    print(f"Error reading region_centroids.csv: {str(e)}")
    sys.exit()

# Read polynomial fits
try:
    with open('polynomial_fits.json', 'r') as f:
        polynomial_fits = json.load(f)
    print(f"Loaded {len(polynomial_fits['fits'])} polynomial fits")
except Exception as e:
    print(f"Error reading polynomial_fits.json: {str(e)}")
    sys.exit()

# Merge mapping and centroids
merged_df = pd.merge(mapping_df, centroids_df, left_on='centroid name', right_on='name', how='left')

# Filter to zones with demand data
valid_zones = merged_df[merged_df['demand file'].notna()]
print(f"Found {len(valid_zones)} zones with demand data")

# Read ERA5 data
print("\nReading ERA5 data...")
try:
    era5_ds = xr.open_dataset('era5/combined_era5.nc')
    print("ERA5 data loaded")
except Exception as e:
    print(f"Error reading ERA5 data: {str(e)}")
    sys.exit()

# Initialize results dictionaries
results = {}
baseline_results = {}
current_results = {}
annual_changes = {}
errors = []

# Analyze each zone
for _, zone_data in valid_zones.iterrows():
    try:
        changes, baseline, current = analyze_zone(zone_data, era5_ds, polynomial_fits)
        results[zone_data['centroid name']] = changes
        baseline_results[zone_data['centroid name']] = baseline
        current_results[zone_data['centroid name']] = current
        
        # Calculate annual averages
        annual_baseline = baseline.mean()
        annual_current = current.mean()
        annual_change = changes.mean()
        annual_changes[zone_data['centroid name']] = annual_change
        
    except Exception as e:
        error_msg = f"Error analyzing zone {zone_data['centroid name']}: {str(e)}"
        print(error_msg)
        errors.append(error_msg)
        continue

if not results:
    print("\nNo results were generated. Check the errors above.")
    sys.exit()
    
# Convert absolute change results to DataFrame
results_df = pd.DataFrame(results).T
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
results_df.columns = month_names
results_df['Annual'] = pd.Series(annual_changes)

# Calculate percent changes
baseline_df = pd.DataFrame(baseline_results).T
baseline_df.columns = month_names
baseline_df['Annual'] = baseline_df.mean(axis=1)

current_df = pd.DataFrame(current_results).T
current_df.columns = month_names
current_df['Annual'] = current_df.mean(axis=1)

# Calculate percent changes
percent_changes_df = ((current_df - baseline_df) / baseline_df * 100).round(1)

# Save results
results_df.to_csv('demand_changes_by_zone.csv')
percent_changes_df.to_csv('demand_changes_by_zone_percent.csv')

print("\nAnalysis complete!")
print(f"Absolute changes saved to demand_changes_by_zone.csv")
print(f"Percent changes saved to demand_changes_by_zone_percent.csv")
print(f"Successfully analyzed {len(results)} zones")

if errors:
    print("\nThe following errors occurred:")
    for error in errors:
        print(f"- {error}")
