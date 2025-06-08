#!/usr/bin/env python3
"""
Download RTO demand data from gridstatus.io API

This script downloads total actual load data for all major RTOs using the gridstatus.io API
and saves them as CSV files in the same format as the existing EIA demand files.

Usage:
    python download_rto_demand_gridstatus.py --year 2024 --api-key YOUR_API_KEY

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

# RTO configuration mapping
# Maps RTO names to their gridstatus dataset names and load column names
RTO_CONFIG = {
    'caiso': {
        'dataset': 'caiso_standardized_hourly',
        'load_column': 'load.load',
        'name': 'CAISO'
    },
    'ercot': {
        'dataset': 'ercot_standardized_hourly', 
        'load_column': 'load.load',
        'name': 'ERCOT'
    },
    'isone': {
        'dataset': 'isone_standardized_hourly',
        'load_column': 'load.load', 
        'name': 'ISONE'
    },
    'miso': {
        'dataset': 'miso_standardized_hourly',
        'load_column': 'load.load',
        'name': 'MISO'
    },
    'nyiso': {
        'dataset': 'nyiso_standardized_hourly',
        'load_column': 'load.load',
        'name': 'NYISO'
    },
    'pjm': {
        'dataset': 'pjm_standardized_hourly',
        'load_column': 'load.load',
        'name': 'PJM'
    },
    'spp': {
        'dataset': 'spp_standardized_hourly',
        'load_column': 'load.load',
        'name': 'SPP'
    }
}

def download_rto_data(client, rto_key, year, output_dir='gridstatus_demand'):
    """
    Download demand data for a specific RTO and year
    
    Parameters:
    -----------
    client : GridStatusClient
        Authenticated gridstatus client
    rto_key : str
        RTO key from RTO_CONFIG
    year : int
        Year to download data for
    output_dir : str
        Directory to save CSV files
    """
    
    config = RTO_CONFIG[rto_key]
    
    print(f"\nDownloading {config['name']} data for {year}...")
    
    # Set date range for full year
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    # Calculate approximate limit (365 days * 24 hours + buffer)
    limit_rows = 365 * 24 + 100
    
    try:
        # Download data from gridstatus
        df = client.get_dataset(
            config['dataset'],
            start=start_date,
            end=end_date,
            limit=limit_rows
        )
        
        print(f"Downloaded {len(df)} rows for {config['name']}")
        
        # Process timestamp - convert to local time for the RTO
        if 'interval_start_utc' in df.columns:
            # Convert UTC to local time (this is a simplification - each RTO has different time zones)
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
        
        # Extract load data
        if config['load_column'] in df.columns:
            load_data = df[['timestamp', config['load_column']]].copy()
            load_data = load_data.rename(columns={config['load_column']: f'{config["name"]} Total Actual Load (MW)'})
        else:
            print(f"Warning: Load column '{config['load_column']}' not found in {config['name']} data")
            print(f"Available columns: {df.columns.tolist()}")
            return False
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Format data to match EIA CSV structure
        # Add header rows to match EIA format
        header_lines = [
            f"{config['name']} Hourly Actual Load (megawatt) - Downloaded from gridstatus.io",
            f"Hourly actual load data for {config['name']}",
            f"Source: gridstatus.io API",
            "UTC Timestamp (Interval Ending),Local Timestamp,Local Date,Hour Number," + 
            f"{config['name']} Total Actual Load (MW)"
        ]
        
        # Process the data to match EIA format
        processed_data = []
        for _, row in load_data.iterrows():
            timestamp = row['timestamp']
            load_value = row[f'{config["name"]} Total Actual Load (MW)']
            
            # Create row matching EIA format
            utc_timestamp = timestamp.astimezone(pd.Timestamp.now().tz).strftime('%Y-%m-%d %H:%M:%S')
            local_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            local_date = timestamp.strftime('%Y-%m-%d')
            hour_number = timestamp.hour + 1  # EIA uses 1-24 hour numbering
            
            processed_data.append([
                utc_timestamp,
                local_timestamp, 
                local_date,
                hour_number,
                load_value
            ])
        
        # Create DataFrame with processed data
        processed_df = pd.DataFrame(processed_data, columns=[
            'UTC Timestamp (Interval Ending)',
            'Local Timestamp', 
            'Local Date',
            'Hour Number',
            f'{config["name"]} Total Actual Load (MW)'
        ])
        
        # Save to CSV file
        filename = f"{rto_key}_load_act_hr_{year}.csv"
        filepath = os.path.join(output_dir, filename)
        
        # Write header lines and data
        with open(filepath, 'w') as f:
            for header in header_lines:
                f.write(header + '\n')
            
        # Append the data without header
        processed_df.to_csv(filepath, mode='a', index=False, header=False)
        
        print(f"Saved {len(processed_df)} rows to {filepath}")
        return True
        
    except Exception as e:
        print(f"Error downloading {config['name']} data: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Download RTO demand data from gridstatus.io')
    parser.add_argument('--year', type=int, required=True, help='Year to download data for')
    parser.add_argument('--api-key', type=str, required=True, help='GridStatus.io API key')
    parser.add_argument('--output-dir', type=str, default='gridstatus_demand', help='Output directory for CSV files')
    parser.add_argument('--rtos', nargs='+', choices=list(RTO_CONFIG.keys()), 
                       default=list(RTO_CONFIG.keys()), help='RTOs to download (default: all)')
    
    args = parser.parse_args()
    
    print(f"Starting download for year {args.year}")
    print(f"RTOs to download: {', '.join(args.rtos)}")
    print(f"Output directory: {args.output_dir}")
    
    # Initialize GridStatus client
    try:
        client = GridStatusClient(api_key=args.api_key)
        print("Successfully connected to GridStatus.io API")
    except Exception as e:
        print(f"Error connecting to GridStatus.io API: {str(e)}")
        return
    
    # Download data for each RTO
    successful_downloads = 0
    failed_downloads = 0
    
    for rto_key in args.rtos:
        success = download_rto_data(client, rto_key, args.year, args.output_dir)
        if success:
            successful_downloads += 1
        else:
            failed_downloads += 1
    
    print(f"\nDownload complete!")
    print(f"Successful downloads: {successful_downloads}")
    print(f"Failed downloads: {failed_downloads}")
    
    if successful_downloads > 0:
        print(f"\nCSV files saved in '{args.output_dir}' directory")
        print("Files can now be used with the existing RTO_polynomial_fit.py script")
        print("Note: You may need to update the demand directory path in RTO_polynomial_fit.py")

if __name__ == "__main__":
    main() 