import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

# Read mapping file
mapping_df = pd.read_csv('mapping.csv')

# Read centroids file
centroids_df = pd.read_csv('temperature/region_centroids.csv')

# Merge mapping and centroids
merged_df = pd.merge(mapping_df, centroids_df, left_on='centroid name', right_on='name', how='left')

# Get zone region data
zone_data = merged_df[merged_df['centroid name'] == 'Coast'].iloc[0]

# Get demand file and column information from mapping
demand_file = f"demand/{zone_data['demand file']}.csv"
demand_column = zone_data['column name']

# Read ERA5 data
era5_ds = xr.open_dataset('era5/combined_era5.nc')

# Find nearest grid point to zone
zone_lat = zone_data['latitude']
zone_lon = zone_data['longitude']

# Create arrays of all lat/lon points
lats = era5_ds.latitude.values
lons = era5_ds.longitude.values
lon_grid, lat_grid = np.meshgrid(lons, lats)
points = np.column_stack((lat_grid.flatten(), lon_grid.flatten()))
zone_point = np.array([[zone_lat, zone_lon]])

# Extract temperature for nearest point using xarray method = 'nearest'
temp_data = era5_ds['2m_temperature'].sel(
    latitude=zone_lat,
    longitude=zone_lon,
    method='nearest'
)

# Read demand data
demand_df = pd.read_csv(demand_file, skiprows=3)
demand_df['datetime'] = pd.to_datetime(demand_df['UTC Timestamp (Interval Ending)'])
demand_df.set_index('datetime', inplace=True)

# Get demand for the region using the column name from mapping
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

def generate_x(X, date):
    """Generate regressors for the regression of demand vs. temperature"""
    data = pd.DataFrame({
        'Temperature': X,
        'Temperature^2': X**2,
        'Temperature^3': X**3,
        'Temperature^4': X**4,
    }, index=date)

    # Make categorical variable for weekday vs. weekend
    data['category'] = (data.index.weekday < 5).astype(int)  # Weekday = 1, Weekend = 0
    
    # Add constant term
    data['Constant'] = 1

    return data

# Generate features for regression
X = daily_temp.values
data = generate_x(X, daily_demand.index)
y = daily_demand.values

# Perform multivariate least squares fit
model = LinearRegression().fit(data, y)

# Get predictions
y_pred = model.predict(data)

# Calculate average weekday prediction
data_avg = data.copy()
data_avg['category'] = 5/7  # Average between weekday and weekend
y_pred_avg = model.predict(data_avg)

# Calculate RMSE and average error
rmse = np.sqrt(mean_squared_error(y, y_pred))
avg_error = np.mean(y - y_pred)

# Create two-panel plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Sort data for smooth curve plotting
sort_idx = np.argsort(X)
X_sorted = X[sort_idx]
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
weekday_effect_size = model.coef_[-2]  # Coefficient for the weekday/weekend category
textstr2 = f'Weekday Effect: {weekday_effect_size:.2f} GW'
ax1.text(0.05, 0.95, textstr2, transform=ax1.transAxes, fontsize=10,
         verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.5))

# Add panel labels
ax1.text(0.90, 0.09, '(a)', transform=ax1.transAxes, fontsize=20, verticalalignment='top')
ax2.text(0.90, 0.09, '(b)', transform=ax2.transAxes, fontsize=20, verticalalignment='top')

plt.tight_layout()
plt.savefig(f'temp_vs_demand_fit_{zone_data["name"].lower()}.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"Analysis complete! Check temp_vs_demand_fit_{zone_data['name'].lower()}.png for the plot.")
print(f"RMSE: {rmse:.1f} GW")
print(f"Average Error: {avg_error:.1f} GW")
print(f"Weekday Effect: {weekday_effect_size:.2f} GW")