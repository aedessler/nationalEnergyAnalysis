import os
import pandas as pd
import numpy as np
from datetime import datetime
import re

# Set the year to process (2023 or 2024)
year = 2024

# Paths to data directories - updated for gridstatus data
PRICE_DIR = 'gridstatus_price'
DEMAND_DIR = 'gridstatus_demand'
# Output file generated based on selected year
OUTPUT_FILE = f'daily_price_demand_{year}.csv'

# Define RTO-specific total demand column names - updated for gridstatus format
RTO_TOTAL_COLUMNS = {
    'NYISO': 'NYISO Total Actual Load (MW)',
    'ISONE': 'ISONE Total Actual Load (MW)',
    'PJM': 'PJM Total Actual Load (MW)',
    'MISO': 'MISO Total Actual Load (MW)',
    'ERCOT': 'ERCOT Total Actual Load (MW)',
    'CAISO': 'CAISO Total Actual Load (MW)',
    'SPP': 'SPP Total Actual Load (MW)'
}

def get_rto_from_filename(filename):
    # Extract RTO name from filename (everything before the underscore)
    return filename.split('_')[0].upper()

def match_price_demand_files(price_files, demand_files, target_year):
    """Match price and demand files by RTO and specified year"""
    matched_files = []
    
    for price_file in price_files:
        # Extract RTO from price filename
        price_rto = get_rto_from_filename(price_file)
        
        # Look for matching demand file
        for demand_file in demand_files:
            demand_rto = get_rto_from_filename(demand_file)
            
            # If RTOs match and both are from the target year
            if price_rto == demand_rto and str(target_year) in price_file and str(target_year) in demand_file:
                matched_files.append((price_file, demand_file, price_rto))
    
    return matched_files

def process_price_data(price_file):
    """Process price data: average all applicable price columns"""
    # Read price data - gridstatus files have 3 header rows
    price_df = pd.read_csv(os.path.join(PRICE_DIR, price_file), skiprows=3)
    
    # Extract date and hour columns
    price_df['Local Date'] = pd.to_datetime(price_df['Local Date'])
    
    # Get all price columns (columns to the right of "Hour Number")
    hour_col_idx = price_df.columns.get_loc('Hour Number')
    price_cols = price_df.columns[hour_col_idx + 1:]
    
    # For gridstatus data, we typically have one main price column per RTO
    # Calculate average price across all price columns (in case there are multiple)
    price_df['Average Price'] = price_df[price_cols].mean(axis=1)
    
    # Keep only date, hour, and average price
    price_df = price_df[['Local Date', 'Hour Number', 'Average Price']]
    
    return price_df

def process_demand_data(demand_file, rto):
    """Process demand data: extract the total column"""
    # Read demand data - gridstatus files have 3 header rows
    demand_df = pd.read_csv(os.path.join(DEMAND_DIR, demand_file), skiprows=3)
    
    # Extract date and hour columns
    demand_df['Local Date'] = pd.to_datetime(demand_df['Local Date'])
    
    # Find total demand column using the RTO mapping
    total_col = None
    
    # Check if we have a predefined column name for this RTO
    if rto in RTO_TOTAL_COLUMNS:
        expected_col = RTO_TOTAL_COLUMNS[rto]
        if expected_col in demand_df.columns:
            total_col = expected_col
    
    # If not found, try to find the total column by scanning through column names
    if not total_col:
        for col in demand_df.columns:
            if 'total' in col.lower() and 'load' in col.lower():
                total_col = col
                break
    
    if not total_col:
        raise ValueError(f"Could not find total demand column in {demand_file}. Columns: {demand_df.columns}")
    
    # Extract total demand column
    demand_df = demand_df[['Local Date', 'Hour Number', total_col]]
    demand_df.rename(columns={total_col: 'Total Demand'}, inplace=True)
    
    return demand_df

def calculate_daily_weighted_price(hourly_data):
    """Calculate daily demand-weighted average price"""
    # Calculate weighted price (price * demand)
    hourly_data['Weighted Price'] = hourly_data['Average Price'] * hourly_data['Total Demand']
    
    # Count number of entries per day
    daily_counts = hourly_data.groupby('Local Date').size()
    
    # Only keep days with 24 entries
    complete_days = daily_counts[daily_counts == 24].index
    hourly_data_filtered = hourly_data[hourly_data['Local Date'].isin(complete_days)]
    
    # Group by date and calculate daily statistics
    daily_data = hourly_data_filtered.groupby('Local Date').agg({
        'Average Price': 'mean',  # Simple average price
        'Total Demand': 'sum',    # Total daily demand
        'Weighted Price': 'sum'   # Sum of weighted prices
    })
    
    # Calculate demand-weighted average price
    daily_data['Demand-Weighted Avg Price'] = daily_data['Weighted Price'] / daily_data['Total Demand']
    daily_data['Total Demand'] = daily_data['Total Demand'] / 24 ## calculate average demand
    # Drop intermediate calculation column
    daily_data.drop('Weighted Price', axis=1, inplace=True)
    
    return daily_data

def main():
    # Get list of price and demand files
    price_files = [f for f in os.listdir(PRICE_DIR) if f.endswith('.csv') and str(year) in f]
    demand_files = [f for f in os.listdir(DEMAND_DIR) if f.endswith('.csv') and str(year) in f]
    
    print(f"Processing data for {year}...")
    print(f"Found {len(price_files)} price files and {len(demand_files)} demand files.")
    
    # Match price and demand files
    matched_files = match_price_demand_files(price_files, demand_files, year)
    
    if not matched_files:
        print(f"No matching price and demand files found for {year}.")
        return
    
    print(f"Found {len(matched_files)} matching RTO pairs:")
    for price_file, demand_file, rto in matched_files:
        print(f"  {rto}: {price_file} + {demand_file}")
    
    # Process each RTO's data
    all_daily_data = []
    
    for price_file, demand_file, rto in matched_files:
        print(f"Processing {rto}...")
        
        try:
            # Process price and demand data
            price_df = process_price_data(price_file)
            demand_df = process_demand_data(demand_file, rto)
            
            # Merge price and demand data
            hourly_data = pd.merge(price_df, demand_df, on=['Local Date', 'Hour Number'])
            
            # Calculate daily weighted average price
            daily_data = calculate_daily_weighted_price(hourly_data)
            
            # Add RTO column
            daily_data['RTO'] = rto
            
            # Add to list of all RTOs
            all_daily_data.append(daily_data)
            
            print(f"  Successfully processed {len(daily_data)} days of data for {rto}")
            
        except Exception as e:
            print(f"Error processing {rto}: {e}")
    
    if not all_daily_data:
        print("No data was processed successfully.")
        return
    
    # Combine all RTOs' data
    combined_daily_data = pd.concat(all_daily_data)
    
    # Reset index to make date a column
    combined_daily_data = combined_daily_data.reset_index()
    
    # Save to CSV
    # Drop Average Price column and round to 4 significant figures
    combined_daily_data = combined_daily_data.drop('Average Price', axis=1)
    for col in ['Total Demand', 'Demand-Weighted Avg Price']:
        combined_daily_data[col] = combined_daily_data[col].apply(lambda x: float(f'{x:.4g}'))
    # Convert MW to GW before saving
    combined_daily_data['Total Demand'] = combined_daily_data['Total Demand'] / 1000
    combined_daily_data.to_csv(OUTPUT_FILE, index=False)
    print(f"Daily price and demand data saved to {OUTPUT_FILE}")
    print(f"Total records: {len(combined_daily_data)}")

if __name__ == "__main__":
    main() 