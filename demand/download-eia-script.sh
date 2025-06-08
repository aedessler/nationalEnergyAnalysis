#!/bin/bash

# Base URL for EIA wholesale electricity market data
base_url="https://www.eia.gov/electricity/wholesalemarkets/csv/"

# Array of filenames from the image, with year changed from 2023 to 2024
# Note: Adding .csv extension to all files for consistency
files=(
    "caiso_load_act_hr_2024.csv"
    "ercot_load_act_hr_2024.csv"
    "isone_load_actr_hr_2024.csv"
    "miso_load_act_hr_2024.csv"
    "nyiso_load_act_hr_2024.csv"
    "pjm_load_act_hr_2024.csv"
    "spp_load_act_hr_2024.csv"
)

# Create directory for downloads if it doesn't exist
mkdir -p eia_data_2024

# Download each file
for file in "${files[@]}"; do
    echo "Downloading $file..."
    wget -P eia_data_2024 "${base_url}${file}"
    
    # Check if download was successful
    if [ $? -eq 0 ]; then
        echo "Successfully downloaded $file"
    else
        echo "Failed to download $file"
    fi
done

echo "All download attempts completed!"
