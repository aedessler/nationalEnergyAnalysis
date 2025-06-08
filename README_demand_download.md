# RTO Demand Data Download

This document describes the comprehensive system for downloading RTO demand data from gridstatus.io, including both Python scripts and bash automation tools.

## Overview

This system provides two main approaches for downloading RTO demand data:

1. **Python Script** (`download_rto_demand_gridstatus.py`) - Direct Python interface
2. **Bash Script** (`download_all_rtos.sh`) - Automated bash wrapper with enhanced features

Both methods download total actual load data for all major RTOs using the gridstatus.io API and save them as CSV files compatible with existing EIA demand file formats.

## Supported RTOs

| Code | Full Name | Timezone |
|------|-----------|----------|
| `caiso` | California Independent System Operator | US/Pacific |
| `ercot` | Electric Reliability Council of Texas | US/Central |
| `isone` | ISO New England | US/Eastern |
| `miso` | Midcontinent Independent System Operator | US/Central |
| `nyiso` | New York Independent System Operator | US/Eastern |
| `pjm` | PJM Interconnection | US/Eastern |
| `spp` | Southwest Power Pool | US/Central |

## Requirements

### GridStatus.io API Key
1. Visit [https://www.gridstatus.io/](https://www.gridstatus.io/)
2. Sign up for an account
3. Get your API key from the dashboard

## Quick Start

### Method 1: Bash Script (Recommended)

#### 1. Set Your API Key
```bash
export GRIDSTATUS_API_KEY='your_api_key_here'
```

#### 2. Download All RTOs (Default)
```bash
./download_all_rtos.sh
```

#### 3. Download Specific RTOs
```bash
./download_all_rtos.sh caiso ercot pjm
```

### Method 2: Python Script (Direct)

#### Download All RTOs
```bash
python download_rto_demand_gridstatus.py --year 2024 --api-key YOUR_API_KEY
```

#### Download Specific RTOs
```bash
python download_rto_demand_gridstatus.py --year 2024 --api-key YOUR_API_KEY --rtos caiso ercot pjm
```

## Bash Script Features

The `download_all_rtos.sh` script provides enhanced functionality:

### 🔍 **Prerequisite Checking**
- Verifies Python installation
- Checks for required Python script
- Auto-installs gridstatusio library if missing

### 📊 **Progress Tracking**
- Colored output for easy reading
- Real-time progress updates
- Download speed and status reporting

### 📝 **Comprehensive Logging**
- Timestamped log files
- All output saved for review
- Error tracking and reporting

### 📈 **Summary Reports**
- File size and line count for each RTO
- Success/failure status
- Next steps guidance

### 🛡️ **Error Handling**
- Graceful failure handling
- Continues with other RTOs if one fails
- Clear error messages and suggestions

## Command Line Options

### Bash Script Options

| Option | Description | Default |
|--------|-------------|---------|
| `-h, --help` | Show help message | - |
| `-y, --year` | Year to download | 2024 |
| `-k, --api-key` | GridStatus.io API key | From GRIDSTATUS_API_KEY env var |
| `-o, --output` | Output directory | gridstatus_demand |
| `-l, --list` | List available RTOs | - |

### Python Script Options

- `--year` (required): Year to download data for
- `--api-key` (required): Your GridStatus.io API key
- `--output-dir` (optional): Output directory for CSV files (default: 'gridstatus_demand')
- `--rtos` (optional): Specific RTOs to download (default: all RTOs)

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GRIDSTATUS_API_KEY` | Your GridStatus.io API key | Yes |

## Usage Examples

### Setting Up API Key
```bash
# Method 1: Environment variable (recommended)
export GRIDSTATUS_API_KEY='your_api_key_here'

# Method 2: Create .env file
echo "GRIDSTATUS_API_KEY=your_api_key_here" > .env
source .env

# Method 3: Set for current session only
GRIDSTATUS_API_KEY='your_key' ./download_all_rtos.sh
```

### Bash Script Examples
```bash
# Download all RTOs for 2024 (default)
./download_all_rtos.sh

# Download only CAISO and ERCOT
./download_all_rtos.sh caiso ercot

# Download all RTOs for 2023
./download_all_rtos.sh -y 2023

# Download CAISO and PJM for 2023
./download_all_rtos.sh -y 2023 caiso pjm

# Use custom output directory
./download_all_rtos.sh -o my_data_dir

# Override API key for one command
./download_all_rtos.sh -k different_api_key caiso

# List available RTOs
./download_all_rtos.sh --list
```

### Python Script Examples
```bash
# Download all RTOs for 2024
python download_rto_demand_gridstatus.py --year 2024 --api-key YOUR_API_KEY

# Download specific RTOs
python download_rto_demand_gridstatus.py --year 2024 --api-key YOUR_API_KEY --rtos ercot

# Download multiple RTOs
python download_rto_demand_gridstatus.py --year 2024 --api-key YOUR_API_KEY --rtos caiso ercot pjm

# Custom output directory
python download_rto_demand_gridstatus.py --year 2024 --api-key YOUR_API_KEY --output-dir my_demand_data
```

## Output

### Files Created
The scripts create CSV files in the specified output directory:
```
gridstatus_demand/
├── caiso_load_act_hr_2024.csv
├── ercot_load_act_hr_2024.csv
├── isone_load_act_hr_2024.csv
├── miso_load_act_hr_2024.csv
├── nyiso_load_act_hr_2024.csv
├── pjm_load_act_hr_2024.csv
└── spp_load_act_hr_2024.csv
```

### Log Files (Bash Script Only)
Each bash script run creates a timestamped log file:
```
download_rtos_20240607_133606.log
```

### Expected Data
- **8,764 lines** per file (4 header + 8,760 data rows)
- **~590-610 KB** per file
- **Full year** of hourly data (365 days × 24 hours for 2024)

## Output Format

The scripts create CSV files with the same format as existing EIA files:

- **Filename format:** `{rto}_load_act_hr_{year}.csv`
- **Examples:** `caiso_load_act_hr_2024.csv`, `ercot_load_act_hr_2024.csv`

Each CSV file includes:
- Header rows with metadata (matching EIA format)
- Columns: UTC Timestamp, Local Timestamp, Local Date, Hour Number, Total Actual Load (MW)
- Timezone-appropriate local timestamps for each RTO

## Data Processing Details

### Timezone Handling
The scripts automatically handle timezone conversion:
- **CAISO:** US/Pacific
- **ERCOT:** US/Central  
- **ISONE, NYISO, PJM:** US/Eastern
- **MISO, SPP:** US/Central

### Data Structure
The scripts process gridstatus.io data to match the EIA CSV format:
- Converts UTC timestamps to appropriate local time zones
- Adds hour numbering (1-24 format used by EIA)
- Includes proper header rows for compatibility

## Integration with Existing Code

The downloaded CSV files are fully compatible with existing analysis scripts. After downloading:

1. **Update the directory path** in `RTO_polynomial_fit.py`:
   ```python
   demand_dir = 'gridstatus_demand'  # Change from 'demand'
   ```

2. **Run your analysis**:
   ```bash
   python RTO_polynomial_fit.py
   ```

3. **Run climate change analysis**:
   ```bash
   python RTO_climate_change_demand_impact.py
   ```

## Sample Output (Bash Script)

```bash
$ ./download_all_rtos.sh caiso ercot

==================================================
  RTO Demand Data Download Script
  GridStatus.io API
==================================================

[2024-06-07 13:35:41] Checking prerequisites...
[SUCCESS] All prerequisites met

[2024-06-07 13:35:42] Starting download for specific RTOs: caiso ercot
[2024-06-07 13:35:42] Year: 2024
[2024-06-07 13:35:42] Output directory: gridstatus_demand

Downloading CAISO data for 2024...
Downloaded 8760 rows for CAISO
Saved 8760 rows to gridstatus_demand/caiso_load_act_hr_2024.csv

Downloading ERCOT data for 2024...
Downloaded 8760 rows for ERCOT
Saved 8760 rows to gridstatus_demand/ercot_load_act_hr_2024.csv

[SUCCESS] Download completed successfully

[2024-06-07 13:35:45] Download Summary:
[SUCCESS] caiso: 8764 lines, 592K
[SUCCESS] ercot: 8764 lines, 590K

[2024-06-07 13:35:45] Next steps:
  1. Review the downloaded files in 'gridstatus_demand'
  2. Update RTO_polynomial_fit.py to use 'gridstatus_demand' directory
  3. Run your analysis: python RTO_polynomial_fit.py
```

## Advantages over EIA Files

- **Real-time access:** No need to manually download and update files
- **Consistent format:** Standardized data structure across all RTOs
- **Automated updates:** Easy to get latest data for any year
- **Selective downloads:** Choose specific RTOs as needed
- **Enhanced automation:** Bash script provides comprehensive workflow management

## Troubleshooting

### Common Issues

1. **API key not found**
   ```bash
   export GRIDSTATUS_API_KEY='your_api_key_here'
   # Or check if it's set: echo $GRIDSTATUS_API_KEY
   ```

2. **Permission denied (bash script)**
   ```bash
   chmod +x download_all_rtos.sh
   ```

3. **Python not found**
   - Ensure Python is installed and in PATH
   - Try `python3` instead of `python`

4. **"gridstatusio library not found"**
   - Install with: `pip install gridstatusio`

5. **API authentication errors**
   - Verify your API key is correct
   - Check your gridstatus.io account status
   - Try setting the key with `-k` option

6. **Network issues**
   - Check internet connection
   - Verify gridstatus.io service status

7. **Missing data for specific RTOs**
   - Some RTOs may have limited historical data availability
   - Check the gridstatus.io documentation for data coverage

8. **Timezone issues**
   - The scripts handle timezone conversion automatically
   - Local timestamps should match the RTO's operating timezone

### Getting Help

- Run `./download_all_rtos.sh --help` for bash script usage information
- Check the log files for detailed error messages (bash script)
- Review the gridstatus.io documentation: [https://docs.gridstatus.io/](https://docs.gridstatus.io/)
- Examine the example usage script: `python example_usage.py`
- Examine existing CSV files in the `demand/` directory for format reference

## Performance

- **Download time**: ~10-15 seconds for all 7 RTOs
- **Total data**: ~4.2 MB for full year of all RTOs
- **API calls**: 1 call per RTO (efficient bulk download)

## Example Workflow

1. **Download data using bash script (recommended):**
   ```bash
   ./download_all_rtos.sh
   ```

   **Or using Python script directly:**
   ```bash
   python download_rto_demand_gridstatus.py --year 2024 --api-key YOUR_API_KEY
   ```

2. **Run polynomial fitting:**
   ```bash
   python RTO_polynomial_fit.py
   ```

3. **Run climate change analysis:**
   ```bash
   python RTO_climate_change_demand_impact.py
   ```
``` 