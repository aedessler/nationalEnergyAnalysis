#!/usr/bin/env python3
"""
Download RTO wholesale price data from gridstatus.io API

This script downloads wholesale electricity price data for all major RTOs using the gridstatus.io API
and saves them as CSV files in a format compatible with existing analysis scripts.

Usage:
    python download_rto_prices_gridstatus.py --year 2024 --api-key YOUR_API_KEY

Requirements:
    - gridstatusio library (pip install gridstatusio)
    - Valid gridstatus.io API key
"""

import pandas as pd
import os
import argparse
from datetime import datetime
import sys
from gridstatusio import GridStatusClient

# RTO price configuration mapping
# Maps RTO names to their gridstatus price dataset names and specific locations to match EIA data
RTO_PRICE_CONFIG = {
    'caiso': {
        'dataset': 'caiso_lmp_day_ahead_hourly',
        'price_column': 'lmp',
        'location_filter': ['TH_NP15_GEN-APND', 'TH_SP15_GEN-APND', 'TH_ZP26_GEN-APND'],  # CAISO trading hub zones
        'name': 'CAISO',
        'market_type': 'Day-Ahead'
    },
    'ercot': {
        'dataset': 'ercot_spp_day_ahead_hourly',
        'price_column': 'spp',
        'location_filter': 'HB_HUBAVG',  # ERCOT hub average (already averaged)
        'name': 'ERCOT',
        'market_type': 'Day-Ahead'
    },
    'isone': {
        'dataset': 'isone_lmp_day_ahead_hourly',
        'price_column': 'lmp',
        'location_filter': ['.H.INTERNAL_HUB', '.Z.CONNECTICUT', '.Z.MAINE', '.Z.NEWHAMPSHIRE', '.Z.RHODEISLAND', '.Z.VERMONT', '.Z.SEMASS', '.Z.WCMASS', '.Z.NEMASSBOST'],  # ISONE zones from gridstatus
        'name': 'ISONE',
        'market_type': 'Day-Ahead'
    },
    'miso': {
        'dataset': 'miso_lmp_day_ahead_hourly',
        'price_column': 'lmp',
        'location_filter': ['ARKANSAS.HUB', 'ILLINOIS.HUB', 'INDIANA.HUB', 'LOUISIANA.HUB', 'MICHIGAN.HUB', 'MINN.HUB', 'MS.HUB', 'TEXAS.HUB'],  # MISO hubs from gridstatus
        'name': 'MISO',
        'market_type': 'Day-Ahead'
    },
    'nyiso': {
        'dataset': 'nyiso_lmp_day_ahead_hourly',
        'price_column': 'lmp',
        'location_filter': ['WEST', 'GENESE', 'CENTRL', 'NORTH', 'MHK VL', 'CAPITL', 'HUD VL', 'MILLWD', 'DUNWOD', 'N.Y.C.', 'LONGIL'],  # NYISO zones A-K
        'name': 'NYISO',
        'market_type': 'Day-Ahead'
    },
    'pjm': {
        'dataset': 'pjm_lmp_day_ahead_hourly',
        'price_column': 'lmp',
        'location_filter': ['AEP GEN HUB', 'ATSI GEN HUB', 'CHICAGO GEN HUB', 'DOMINION HUB', 'EASTERN HUB', 'NEW JERSEY HUB', 'OHIO HUB'],  # PJM hubs from gridstatus
        'name': 'PJM',
        'market_type': 'Day-Ahead'
    },
    'spp': {
        'dataset': 'spp_lmp_day_ahead_hourly',
        'price_column': 'lmp',
        'location_filter': ['SPPNORTH_HUB', 'SPPSOUTH_HUB'],  # Use North and South hubs
        'name': 'SPP',
        'market_type': 'Day-Ahead'
    }
}

def download_rto_price_data(client, rto_key, year, output_dir='gridstatus_price'):
    """
    Download price data for a specific RTO and year
    
    Parameters:
    -----------
    client : GridStatusClient
        Authenticated gridstatus client
    rto_key : str
        RTO key from RTO_PRICE_CONFIG
    year : int
        Year to download data for
    output_dir : str
        Directory to save CSV files
    """
    
    config = RTO_PRICE_CONFIG[rto_key]
    
    print(f"\nDownloading {config['name']} price data for {year}...")
    print(f"Dataset: {config['dataset']}")
    print(f"Market Type: {config['market_type']}")
    
    # Set date range for full year
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    try:
        # Download data from gridstatus - all RTOs now have specific location filters
        if isinstance(config['location_filter'], list):
            # For RTOs with multiple specific locations/hubs, download and average them
            print(f"Fetching data for specific locations: {config['location_filter']}")
            limit_rows = 365 * 24 * len(config['location_filter']) + 100
            
            location_data = []
            for location in config['location_filter']:
                print(f"  Downloading {location}...")
                df_location = client.get_dataset(
                    config['dataset'],
                    start=start_date,
                    end=end_date,
                    filter_column="location",
                    filter_value=location,
                    limit=limit_rows
                )
                if len(df_location) > 0:
                    location_data.append(df_location)
                    print(f"    Downloaded {len(df_location)} rows for {location}")
                else:
                    print(f"    No data found for {location}")
            
            if not location_data:
                print(f"No data found for any locations in {config['name']}")
                return False
            
            # Combine location data and calculate average
            df_all_locations = pd.concat(location_data, ignore_index=True)
            print(f"Calculating average across {len(config['location_filter'])} locations...")
            
            price_col = config['price_column']
            df_avg = df_all_locations.groupby('interval_start_utc')[price_col].mean().reset_index()
            
            # Add back other columns
            df_avg['location'] = f"{config['name']}_AVERAGE"
            df_avg['market'] = df_all_locations['market'].iloc[0] if 'market' in df_all_locations.columns else config['market_type']
            
            df = df_avg
            print(f"Calculated location average for {len(df)} time periods")
            
        else:
            # For ERCOT, use the single hub average directly
            print(f"Fetching data with location filter: {config['location_filter']}")
            limit_rows = 365 * 24 + 100
            df = client.get_dataset(
                config['dataset'],
                start=start_date,
                end=end_date,
                filter_column="location",
                filter_value=config['location_filter'],
                limit=limit_rows
            )
            print(f"Downloaded {len(df)} rows for {config['name']}")
            
            if len(df) == 0:
                print(f"No data found for {config['name']}")
                return False
        
        # Process timestamp - convert to local time for the RTO
        if 'interval_start_utc' in df.columns:
            df['timestamp'] = pd.to_datetime(df['interval_start_utc'])
            
            # Apply timezone conversion based on RTO
            if rto_key == 'caiso':
                df['timestamp'] = df['timestamp'].dt.tz_convert('US/Pacific')
            elif rto_key == 'ercot':
                df['timestamp'] = df['timestamp'].dt.tz_convert('US/Central')
            elif rto_key in ['isone', 'nyiso']:
                df['timestamp'] = df['timestamp'].dt.tz_convert('US/Eastern')
            elif rto_key == 'miso':
                df['timestamp'] = df['timestamp'].dt.tz_convert('US/Central')
            elif rto_key == 'pjm':
                df['timestamp'] = df['timestamp'].dt.tz_convert('US/Eastern')
            elif rto_key == 'spp':
                df['timestamp'] = df['timestamp'].dt.tz_convert('US/Central')
        
        # Extract price data
        price_col = config['price_column']
        if price_col in df.columns:
            price_data = df[['timestamp', price_col]].copy()
            
            # Rename price column to standardized format
            price_data = price_data.rename(columns={
                price_col: f'{config["name"]} {config["market_type"]} Price ($/MWh)'
            })
        else:
            print(f"Warning: Price column '{price_col}' not found in {config['name']} data")
            print(f"Available columns: {df.columns.tolist()}")
            return False
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Format data to match existing price file structure
        if isinstance(config['location_filter'], list):
            # Multiple locations/hubs
            location_desc = f"Average of specific locations ({', '.join(config['location_filter'])})"
        else:
            # Single hub (like ERCOT)
            location_desc = f"Hub Average ({config['location_filter']})"
            
        header_lines = [
            f"{config['name']} Hourly {config['market_type']} Prices ($/MWh) - Downloaded from gridstatus.io",
            f"Hourly {config['market_type'].lower()} price data for {config['name']} - {location_desc}",
            f"Source: gridstatus.io API - Dataset: {config['dataset']}",
            "UTC Timestamp (Interval Ending),Local Timestamp,Local Date,Hour Number," + 
            f"{config['name']} {config['market_type']} Price ($/MWh)"
        ]
        
        # Process the data to match existing format
        processed_data = []
        for _, row in price_data.iterrows():
            timestamp = row['timestamp']
            price_value = row[f'{config["name"]} {config["market_type"]} Price ($/MWh)']
            
            # Skip rows with missing price data
            if pd.isna(price_value):
                continue
            
            # Create row matching existing format
            utc_timestamp = timestamp.astimezone(pd.Timestamp.now().tz).strftime('%Y-%m-%d %H:%M:%S')
            local_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            local_date = timestamp.strftime('%Y-%m-%d')
            hour_number = timestamp.hour + 1  # Use 1-24 hour numbering
            
            processed_data.append([
                utc_timestamp,
                local_timestamp, 
                local_date,
                hour_number,
                price_value
            ])
        
        # Create DataFrame with processed data
        processed_df = pd.DataFrame(processed_data, columns=[
            'UTC Timestamp (Interval Ending)',
            'Local Timestamp', 
            'Local Date',
            'Hour Number',
            f'{config["name"]} {config["market_type"]} Price ($/MWh)'
        ])
        
        # Save to CSV file
        filename = f"{rto_key}_price_{config['market_type'].lower().replace('-', '_')}_hr_{year}.csv"
        filepath = os.path.join(output_dir, filename)
        
        # Write header lines and data
        with open(filepath, 'w') as f:
            for header in header_lines:
                f.write(header + '\n')
            
        # Append the data without header
        processed_df.to_csv(filepath, mode='a', index=False, header=False)
        
        print(f"Saved {len(processed_df)} rows to {filepath}")
        
        # Print price statistics
        prices = processed_df[f'{config["name"]} {config["market_type"]} Price ($/MWh)']
        print(f"Price statistics: Min=${prices.min():.2f}, Max=${prices.max():.2f}, Avg=${prices.mean():.2f}")
        
        return True
        
    except Exception as e:
        print(f"Error downloading {config['name']} price data: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Download RTO wholesale price data from gridstatus.io')
    parser.add_argument('--year', type=int, required=True, help='Year to download data for')
    parser.add_argument('--api-key', type=str, help='GridStatus.io API key (or set GRIDSTATUS_API_KEY env var)')
    parser.add_argument('--output-dir', type=str, default='gridstatus_price', help='Output directory for CSV files')
    parser.add_argument('--rtos', nargs='+', choices=list(RTO_PRICE_CONFIG.keys()), 
                       default=list(RTO_PRICE_CONFIG.keys()), help='RTOs to download (default: all)')
    
    args = parser.parse_args()
    
    # Get API key from argument or environment variable
    api_key = args.api_key or os.environ.get('GRIDSTATUS_API_KEY')
    if not api_key:
        print("Error: GridStatus.io API key not found!")
        print("Please provide API key via --api-key argument or set GRIDSTATUS_API_KEY environment variable")
        return
    
    print(f"Starting price data download for year {args.year}")
    print(f"RTOs to download: {', '.join(args.rtos)}")
    print(f"Output directory: {args.output_dir}")
    
    # Initialize GridStatus client
    try:
        client = GridStatusClient(api_key=api_key)
        print("Successfully connected to GridStatus.io API")
    except Exception as e:
        print(f"Error connecting to GridStatus.io API: {str(e)}")
        return
    
    # Download data for each RTO
    successful_downloads = 0
    failed_downloads = 0
    
    for rto_key in args.rtos:
        success = download_rto_price_data(client, rto_key, args.year, args.output_dir)
        if success:
            successful_downloads += 1
        else:
            failed_downloads += 1
    
    print(f"\nPrice data download complete!")
    print(f"Successful downloads: {successful_downloads}")
    print(f"Failed downloads: {failed_downloads}")
    
    if successful_downloads > 0:
        print(f"\nCSV files saved in '{args.output_dir}' directory")
        print("Files can be used for price analysis and demand-price correlation studies")

if __name__ == "__main__":
    main() 