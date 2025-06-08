import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Define the years range
years = range(2010, 2025)

# List to store all August price data
all_august_data = []

# Loop through each year
for year in years:
    try:
        # Path to the day ahead price file
        price_file = f'../../ERCOT/priceData/day ahead prices/rpt.00013060.0000000000000000.DAMLZHBSPP_{year}.xlsx'
        
        # Path to the demand file
        demand_file = f'../../ERCOT/loadData/Native_Load_{year}.xlsx'
        
        # Check if price file exists
        if not os.path.exists(price_file):
            print(f"Price data file for {year} not found: {price_file}")
            continue
            
        # Check if demand file exists
        if not os.path.exists(demand_file):
            print(f"Demand data file for {year} not found: {demand_file}")
            continue
        
        # Read the price Excel file, focusing on August sheet
        try:
            price_data = pd.read_excel(price_file, sheet_name='Aug')
            print(f"Successfully read August price data for {year}")
        except Exception as e:
            print(f"Could not read August sheet for {year}: {e}")
            continue
        
        # Filter for HB_HUBAVG (hub average price)
        hub_prices = price_data[price_data['Settlement Point'] == 'HB_HUBAVG'].copy()
        
        if hub_prices.empty:
            print(f"No HB_HUBAVG data found for {year}")
            continue
            
        # Extract hour from the Hour Ending column which is in format "HH:00"
        # Parse the hour directly from the string format (e.g., "01:00" → 1)
        hub_prices['hour'] = hub_prices['Hour Ending'].str.extract(r'(\d+):').astype(int)
        
        # Handle hour 24 (midnight) - convert to hour 0
        hub_prices.loc[hub_prices['hour'] == 24, 'hour'] = 0
        
        # Read the demand Excel file
        try:
            demand_data = pd.read_excel(demand_file, usecols=['Hour Ending', 'ERCOT'])
            print(f"Successfully read demand data for {year}")
        except Exception as e:
            print(f"Could not read demand data for {year}: {e}")
            continue
        
        # Convert Hour Ending to datetime
        demand_data['Hour Ending'] = demand_data['Hour Ending'].astype('string')
        
        # Process demand timestamps similar to create_price_demand.py
        demand_data['Hour Ending'] = demand_data['Hour Ending'].str.replace(' 24:', ' 00:')
        demand_data['Hour Ending'] = demand_data['Hour Ending'].str.replace(' DST', '')
        
        try:
            demand_data['Hour Ending'] = pd.to_datetime(demand_data['Hour Ending'])
            
            # Handle midnight adjustment (add a day for midnight entries)
            demand_data.loc[demand_data['Hour Ending'].dt.strftime('%H:%M:%S') == '00:00:00', 'Hour Ending'] += timedelta(days=1)
            
            # Convert demand to GW
            demand_data['ERCOT'] /= 1e3
            
            # Filter for August data only
            demand_data['month'] = demand_data['Hour Ending'].dt.month
            august_demand = demand_data[demand_data['month'] == 8].copy()
            
            # Extract hour from the Hour Ending
            august_demand['hour'] = august_demand['Hour Ending'].dt.hour
            
            # Convert hour 0 to 24 for consistency with price data
            august_demand.loc[august_demand['hour'] == 0, 'hour'] = 24
            
            print(f"Processed demand data for August {year}")
        except Exception as e:
            print(f"Error processing demand timestamps for {year}: {e}")
            continue
        
        # Add year column for potential multi-year analysis
        hub_prices['year'] = year
        august_demand['year'] = year
        
        # Aggregate demand by hour
        hourly_demand = august_demand.groupby(['year', 'hour'])['ERCOT'].mean().reset_index()
        
        # Merge price and demand data
        merged_data = pd.merge(hub_prices[['hour', 'year', 'Settlement Point Price']], 
                               hourly_demand[['hour', 'year', 'ERCOT']], 
                               on=['hour', 'year'], how='left')
        
        # Append to our list
        all_august_data.append(merged_data)
        
        print(f"Processed data for August {year}")
        
    except Exception as e:
        print(f"Error processing {year}: {e}")

# Combine all data if we have any
if all_august_data:
    # Combine all years of data
    august_prices = pd.concat(all_august_data, ignore_index=True)
    
    # Get year range for title
    start_year = august_prices['year'].min()
    end_year = august_prices['year'].max()
    
    # Count how many years of data we have
    year_count = august_prices['year'].nunique()
    print(f"Analysis includes {year_count} years of data from {start_year} to {end_year}")
    
    # Calculate hourly averages for each year (for CSV export)
    yearly_hourly_prices = august_prices.groupby(['year', 'hour']).agg({
        'Settlement Point Price': 'mean',
        'ERCOT': 'mean'
    }).reset_index()
    
    # Handle hour 0 (midnight) for display purposes
    # Create a copy with hour 0 changed to hour 24
    display_yearly_hourly = yearly_hourly_prices.copy()
    display_yearly_hourly.loc[display_yearly_hourly['hour'] == 0, 'hour'] = 24
    display_yearly_hourly = display_yearly_hourly.sort_values(['year', 'hour'])
    
    # Save the yearly hourly data to CSV
    display_yearly_hourly.to_csv('august_hourly_prices_by_year.csv', index=False)
    print("Yearly hourly prices saved to 'august_hourly_prices_by_year.csv'")
    
    # Also calculate overall averages across all years
    hourly_avg_prices = august_prices.groupby('hour').agg({
        'Settlement Point Price': 'mean',
        'ERCOT': 'mean'
    }).reset_index()
    
    # Also calculate standard deviation for error bars
    hourly_std = august_prices.groupby('hour').agg({
        'Settlement Point Price': 'std',
        'ERCOT': 'std'
    }).reset_index()
    
    hourly_avg_prices['price_std'] = hourly_std['Settlement Point Price']
    hourly_avg_prices['demand_std'] = hourly_std['ERCOT']
    
    # Get min and max prices and demand for each hour
    hourly_min = august_prices.groupby('hour').agg({
        'Settlement Point Price': 'min',
        'ERCOT': 'min'
    }).reset_index()
    
    hourly_max = august_prices.groupby('hour').agg({
        'Settlement Point Price': 'max',
        'ERCOT': 'max'
    }).reset_index()
    
    hourly_avg_prices['price_min'] = hourly_min['Settlement Point Price']
    hourly_avg_prices['price_max'] = hourly_max['Settlement Point Price']
    hourly_avg_prices['demand_min'] = hourly_min['ERCOT']
    hourly_avg_prices['demand_max'] = hourly_max['ERCOT']
    
    # Sort by hour for the CSV
    hourly_avg_prices = hourly_avg_prices.sort_values('hour')
    
    # Reorder so that hour 0 appears at the end as hour 24
    if 0 in hourly_avg_prices['hour'].values:
        midnight_price = hourly_avg_prices[hourly_avg_prices['hour'] == 0].copy()
        midnight_price['hour'] = 24
        hourly_avg_prices = hourly_avg_prices[hourly_avg_prices['hour'] > 0]
        hourly_avg_prices = pd.concat([hourly_avg_prices, midnight_price])
        hourly_avg_prices = hourly_avg_prices.sort_values('hour')
    
    # Save the average hourly prices data to CSV
    hourly_avg_prices.to_csv('august_hourly_prices_avg.csv', index=False)
    print("Average hourly prices saved to 'august_hourly_prices_avg.csv'")
    
    print("Data processing complete.")
    print("To create visualizations, run 'plot_august_prices.py'")
else:
    print("No data was successfully processed.") 