import pandas as pd
import xarray as xr
import numpy as np
from sklearn.linear_model import LinearRegression
import json
import warnings
import matplotlib.pyplot as plt

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
    
    return data

def fit_zone(zone_data, era5_ds):
    """Fit temperature-demand relationship for a single zone and save coefficients"""
    print(f"\nFitting zone: {zone_data['centroid name']}")
    
    # Get demand file and column information
    demand_file = f"demand/{zone_data['demand file']}.csv"
    demand_column = zone_data['column name']
    
    # Get zone coordinates
    zone_lat = zone_data['latitude']
    zone_lon = zone_data['longitude']
    
    # Extract temperature for nearest point
    temp_data = era5_ds['2m_temperature'].sel(
        latitude=zone_lat,
        longitude=zone_lon,
        method='nearest'
    )
    
    # Read current demand data
    demand_df = pd.read_csv(demand_file, skiprows=3)
    demand_df['datetime'] = pd.to_datetime(demand_df.iloc[:,1])
    demand_df.set_index('datetime', inplace=True)
    
    # Get demand for the region and convert to GW
    region_demand = demand_df[demand_column]/1e3
    
    # Calculate daily average demand
    daily_demand = region_demand.resample('D').mean()
    
    # Convert temperature data to pandas series with datetime index
    temp_series = temp_data.to_series()
    daily_temp = temp_series.resample('D').mean()
    
    # Align the dates
    common_dates = daily_demand.index.intersection(daily_temp.index)
    daily_demand = daily_demand[common_dates]
    daily_temp = daily_temp[common_dates]
    
    # Remove any NaN values
    valid_mask = ~(np.isnan(daily_demand) | np.isnan(daily_temp))
    daily_demand = daily_demand[valid_mask]
    daily_temp = daily_temp[valid_mask]
    
    # Remove zero demand days
    nonzero_mask = (daily_demand > 0)
    daily_demand = daily_demand[nonzero_mask]
    daily_temp = daily_temp[nonzero_mask]
    
    if len(daily_demand) < 30:
        raise ValueError(f"Insufficient data: only {len(daily_demand)} valid days")
    
    print(f"Fitting model on {len(daily_demand)} days of data")
    
    # Train model
    X = daily_temp.values
    data = generate_x(X, daily_demand.index)
    y = daily_demand.values
    model = LinearRegression().fit(data, y)
    
    # Get predictions using actual weekday/weekend categories
    y_pred = model.predict(data)
    
    # Calculate fit statistics
    rmse = np.sqrt(np.mean((y - y_pred)**2))
    r2 = model.score(data, y)
    
    # Create two-panel plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Extract RTO name from demand file (part before first underscore)
    rto_name = zone_data['demand file'].split('_')[0].upper()
    
    # Add overall title with zone info
    fig.suptitle(f'Temperature-Demand Relationship for {zone_data["centroid name"]} ({rto_name})\nCentroid: ({zone_lat:.2f}°N, {zone_lon:.2f}°E)', 
                 fontsize=14, y=1.05)
    
    # Sort data for smooth curve plotting
    sort_idx = np.argsort(X)
    X_sorted = X[sort_idx]
    
    # Create separate data for smooth prediction line (using average weekday/weekend effect)
    data_avg = data.copy()
    data_avg['category'] = 5/7  # Average between weekday and weekend for smooth curve only
    y_pred_avg = model.predict(data_avg)
    y_pred_avg_sorted = y_pred_avg[sort_idx]
    
    # Left Panel: Temperature vs Demand
    ax1.scatter(X, y, alpha=0.5, label='Data')
    ax1.plot(X_sorted, y_pred_avg_sorted, color='k', ls='--', lw=2, label='Fit')
    ax1.set_title('Temperature vs Demand')
    ax1.set_xlabel('Daily Avg. Temperature (°C)')
    ax1.set_ylabel('Daily Avg. Demand (GW)')
    ax1.grid(True)
    ax1.legend()
    
    # Right Panel: Predicted vs Actual Demand
    ax2.scatter(y, y_pred, alpha=0.5)
    ax2.plot([min(y), max(y)], [min(y), max(y)], 'k--', lw=2)
    ax2.set_title('Predicted vs Actual Demand')
    ax2.set_xlabel('Actual Daily Avg. Demand (GW)')
    ax2.set_ylabel('Predicted Daily Avg. Demand (GW)')
    ax2.grid(True)
    
    # Add RMSE as text box
    textstr = f'RMSE: {rmse:.1f} GW'
    ax2.text(0.05, 0.95, textstr, transform=ax2.transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.5))
    
    # Add weekday effect size as text box
    weekday_effect_size = model.coef_[4]  # Index 4 corresponds to the weekday/weekend category
    textstr2 = f'Weekday Effect: {weekday_effect_size:.2f} GW'
    # ax1.text(0.05, 0.95, textstr2, transform=ax1.transAxes, fontsize=10,
    #          verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.5))
    
    # Add panel labels
    # ax1.text(0.90, 0.09, '(a)', transform=ax1.transAxes, fontsize=20, verticalalignment='top')
    # ax2.text(0.90, 0.09, '(b)', transform=ax2.transAxes, fontsize=20, verticalalignment='top')
    
    plt.tight_layout()
    plt.savefig(f'plots/temp_vs_demand_fit_{zone_data["centroid name"].lower()}.pdf', 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\nPlot saved as plots/temp_vs_demand_fit_{zone_data['centroid name'].lower()}.pdf")
    print(f"RMSE: {rmse:.1f} GW")
    print(f"Weekday Effect: {weekday_effect_size:.2f} GW")
    
    # Create coefficient dictionary
    coef_dict = {
        'zone_name': zone_data['centroid name'],
        'rto': zone_data['demand file'].split('_')[0].upper(),
        'latitude': float(zone_lat),
        'longitude': float(zone_lon),
        'coefficients': {
            'constant': float(model.intercept_),
            'temperature': float(model.coef_[0]),
            'temperature^2': float(model.coef_[1]),
            'temperature^3': float(model.coef_[2]),
            'temperature^4': float(model.coef_[3]),
            'weekday_effect': float(model.coef_[4])
        },
        'fit_statistics': {
            'rmse_GW': float(rmse),
            'r2': float(r2),
            'n_days': int(len(daily_demand))
        },
        'data_range': {
            'start_date': daily_demand.index.min().strftime('%Y-%m-%d'),
            'end_date': daily_demand.index.max().strftime('%Y-%m-%d'),
            'min_temp_C': float(daily_temp.min()),
            'max_temp_C': float(daily_temp.max()),
            'avg_demand_GW': float(daily_demand.mean()),
            'max_demand_GW': float(daily_demand.max())
        }
    }
    
    return coef_dict

print("Starting polynomial fits...")

# Read mapping file
mapping_df = pd.read_csv('mapping.csv')
print(f"Found {len(mapping_df)} total zones in mapping file")

# Read centroids file
centroids_df = pd.read_csv('temperature/region_centroids.csv')
print(f"Found {len(centroids_df)} zones in centroids file")

# Merge mapping and centroids
merged_df = pd.merge(mapping_df, centroids_df, left_on='centroid name', right_on='name', how='left')

# Filter to zones with demand data
valid_zones = merged_df[merged_df['demand file'].notna()]
print(f"Found {len(valid_zones)} zones with demand data")

# Read ERA5 data
print("\nReading ERA5 data...")
era5_ds = xr.open_dataset('era5/combined_era5.nc')
print("ERA5 data loaded")

# Initialize results list
results = []
errors = []

# Analyze each zone
for _, zone_data in valid_zones.iterrows():
    try:
        coef_dict = fit_zone(zone_data, era5_ds)
        results.append(coef_dict)
        print(f"Successfully fit {zone_data['centroid name']}")

    except Exception as e:
        error_msg = f"Error fitting zone {zone_data['centroid name']}: {str(e)}"
        print(error_msg)
        errors.append(error_msg)
        continue

# Save results to JSON file
output_file = 'polynomial_fits.json'
with open(output_file, 'w') as f:
    json.dump({
        'fits': results,
        'errors': errors,
        'metadata': {
            'n_zones_total': len(valid_zones),
            'n_zones_successful': len(results),
            'n_zones_failed': len(errors)
        }
    }, f, indent=2)

print(f"\nAnalysis complete!")
print(f"Successfully fit {len(results)} zones")
print(f"Results saved to {output_file}")

if errors:
    print("\nThe following errors occurred:")
    for error in errors:
        print(f"- {error}")

