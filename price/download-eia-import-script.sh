#!/bin/bash

# Base URL for EIA wholesale electricity market data
base_url="https://www.eia.gov/electricity/wholesalemarkets/csv/"

# Array of filenames from the image, with year changed from 2023 to 2024
files=(
    "caiso_lmp_da_hr_zones_2024.csv"
    "ercot_lmp_da_hr_hubs_2024.csv"
    "isone_lmp_da_hr_zones_2024.csv"
    "miso_lmp_rt_hr_hubs_2024.csv"
    "nyiso_lmp_rt_hr_zones_2024.csv"
    "pjm_lmp_rt_hr_hubs_2024.csv"
    "spp_lmp_da_hr_hubs_2024.csv"
)

# Create directory for downloads if it doesn't exist
mkdir -p eia_import_data_2024

# Download each file
for file in "${files[@]}"; do
    echo "Downloading $file..."
    wget -P eia_import_data_2024 "${base_url}${file}"
    
    # Check if download was successful
    if [ $? -eq 0 ]; then
        echo "Successfully downloaded $file"
    else
        echo "Failed to download $file"
    fi
done

echo "All download attempts completed!"
