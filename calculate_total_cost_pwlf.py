import pandas as pd
import numpy as np
import json
import xarray as xr
from datetime import datetime
import os

# Configuration
YEAR = 2024  # Year to analyze
POLY_DEGREE = 3  # Degree of polynomial fit to use
SUMMER_MONTHS = [6, 7, 8, 9]  # June through September
print(f'year = {YEAR}')

# RTO name mapping (from file names to short names)
RTO_NAME_MAPPING = {
    'CAISO': 'CALIFORNIA_INDEPENDENT_SYSTEM_OPERATOR',
    'ERCOT': 'ELECTRIC_RELIABILITY_COUNCIL_OF_TEXAS,_INC.',
    'ISONE': 'ISO_NEW_ENGLAND_INC.',
    'MISO': 'MIDCONTINENT_INDEPENDENT_TRANSMISSION_SYSTEM_OPERATOR,_INC..',
    'NYISO': 'NEW_YORK_INDEPENDENT_SYSTEM_OPERATOR',
    'PJM': 'PJM_INTERCONNECTION,_LLC',
    'SPP': 'SOUTHWEST_POWER_POOL'
}

def predict_demand(temp, coefficients, is_weekday=True):
    """Predict demand based on temperature using polynomial fit."""
    # Get minimum temperature from data_range
    min_temp = coefficients.get('data_range', {}).get('min_temp_C', float('-inf'))
    
    # Use minimum temperature as lower bound
    temp = max(temp, min_temp)
    
    weekday_effect = coefficients['weekday_effect'] if is_weekday else 0
    demand = coefficients['constant']
    # First order term
    if POLY_DEGREE >= 1:
        demand += coefficients['temperature'] * temp
    # Higher order terms
    for i in range(2, POLY_DEGREE + 1):
        demand += coefficients[f'temperature^{i}'] * temp**i
    demand += weekday_effect
    return max(0, float(demand))  # Ensure non-negative demand and convert to scalar

def get_price(demand, pwlf_params):
    """Get price for a given demand using piecewise linear fit."""
    breakpoints = pwlf_params['breakpoints']
    slopes = pwlf_params['slopes']
    intercepts = pwlf_params['intercepts']
    
    # For values below minimum breakpoint
    if demand < breakpoints[0]:
        return slopes[0] * demand + intercepts[0]
    
    # For values above maximum breakpoint
    if demand > breakpoints[-1]:
        return slopes[-1] * demand + intercepts[-1]
    
    # Find which segment the demand falls into
    for i in range(len(breakpoints) - 1):
        if breakpoints[i] <= demand <= breakpoints[i + 1]:
            return slopes[i] * demand + intercepts[i]
    
    # This should never happen due to the above checks, but just in case
    return 0

# Load demand-temperature fits
#print("Loading demand-temperature fits...")
filename = f'polynomial_fits_RTO_{YEAR}_degree{POLY_DEGREE}.json'
fits = json.load(open(filename, 'r'))
demand_fits = {fit['rto']: {'coefficients': fit['coefficients'], 'data_range': fit['data_range']} 
              for fit in fits['fits']}

# Load price-demand piecewise linear fits
#print("Loading price-demand piecewise linear fits...")
with open(f'price_demand_pwlf_{YEAR}.json', 'r') as f:
    price_demand = json.load(f)

# Initialize results dictionary
results = {rto: {'total_cost': 0, 'total_demand': 0} for rto in demand_fits.keys()}

# Dictionary to store all RTO temperature and cost data
rto_data = {}

# Process each RTO
for short_name in demand_fits.keys():
    #print(f"\nProcessing {short_name}...")
    
    # Find the corresponding long name
    long_name = RTO_NAME_MAPPING[short_name]
    
    # Get RTO-specific temperatures
    #print(f"Loading temperature data for {short_name}...")
    filename = f'RTO temp calc/weighted_temps/{long_name}_weighted_temp.nc'
    daily_data = xr.open_dataset(filename)
    
    rto_temp = pd.Series(
        daily_data.t2m.values,
        index=pd.to_datetime(daily_data.time.values)
    ).to_frame('temperature')
    
    # Filter for summer months only
    rto_temp = rto_temp[rto_temp.index.month.isin(SUMMER_MONTHS)]
    
    # Add weekday column
    rto_temp['is_weekday'] = rto_temp.index.dayofweek < 5
    
    # Calculate daily demand using the predict_demand function
    rto_temp['daily_demand'] = rto_temp.apply(
        lambda row: predict_demand(
            row['temperature'],
            demand_fits[short_name]['coefficients'],
            row['is_weekday']
        ),
        axis=1
    )
    
    # Calculate daily price using piecewise linear fit
    rto_temp['daily_price'] = rto_temp['daily_demand'].apply(
        lambda demand: get_price(demand, price_demand[short_name])
    )
    
    # Calculate daily cost
    rto_temp['daily_cost'] = rto_temp['daily_demand']*24e3 * rto_temp['daily_price']
    
    # Store the DataFrame in the rto_data dictionary
    rto_data[short_name] = rto_temp

# Create empty lists to store the data
rtos = []
baseline_avgs = []
recent_avgs = []
pct_changes = []

for rto in rto_data.keys():
    # Calculate annual averages
    annual_data = rto_data[rto].groupby(rto_data[rto].index.year)['daily_cost'].sum()
    
    # Calculate average for baseline period (1951-1980)
    baseline_avg = annual_data.loc[1951:1980].mean()
    
    # Calculate average for recent period (2015-2024)
    recent_avg = annual_data.loc[2015:2024].mean()
    
    # Calculate percent change
    pct_change = ((recent_avg - baseline_avg) / baseline_avg) * 100
    
    # Append values to lists
    rtos.append(rto)
    baseline_avgs.append(baseline_avg)
    recent_avgs.append(recent_avg)
    pct_changes.append(pct_change)

# Create DataFrame
results_df = pd.DataFrame({
    'RTO': rtos,
    'baseline': baseline_avgs,
    'recent': recent_avgs,
    'pct_change': pct_changes
})

# Set RTO as index
results_df.set_index('RTO', inplace=True)
results_df['baseline'] /= 1e9
results_df['recent'] /= 1e9
results_df['change'] = results_df.recent - results_df.baseline
results_df = results_df[['baseline', 'recent', 'change','pct_change']]

population_dict = {
    'RTO': ['CAISO', 'ERCOT', 'ISONE', 'MISO', 'NYISO', 'PJM', 'SPP'],
    'population': [32, 26, 15, 45, 20, 65, 19]
}
population_df = pd.DataFrame(population_dict)
population_df.set_index('RTO', inplace=True)

print(results_df)