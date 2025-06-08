# GridStatus.io RTO Price Data Download System

This system downloads wholesale electricity price data from gridstatus.io for Regional Transmission Organizations (RTOs) in the United States. The system consists of a Python script for core functionality and a bash wrapper for enhanced user experience and automation.

## Overview

The system downloads day-ahead wholesale electricity prices for 7 major RTOs:
- **CAISO** (California Independent System Operator)
- **ERCOT** (Electric Reliability Council of Texas)
- **ISONE** (ISO New England)
- **MISO** (Midcontinent Independent System Operator)
- **NYISO** (New York Independent System Operator)
- **PJM** (PJM Interconnection)
- **SPP** (Southwest Power Pool)

## Files

### Core Scripts
- `download_rto_prices_gridstatus.py` - Main Python script for downloading price data
- `download_all_rto_prices.sh` - Bash wrapper with enhanced features and logging

### Output
- CSV files saved to `gridstatus_price/` directory (configurable)
- Files named as: `{rto}_price_day_ahead_hr_{year}.csv`

## Python Script: `download_rto_prices_gridstatus.py`

### Features
- Downloads day-ahead hourly wholesale electricity prices
- Uses specific representative locations/hubs for each RTO (not all locations)
- Calculates RTO-wide averages from multiple hubs/zones where applicable
- Proper timezone conversion for each RTO
- EIA-compatible CSV output format
- Command-line interface with flexible options

### Usage

#### Basic Usage
```bash
python download_rto_prices_gridstatus.py --year 2024 --api-key YOUR_API_KEY
```

#### Advanced Usage
```bash
python download_rto_prices_gridstatus.py \
    --year 2024 \
    --api-key YOUR_API_KEY \
    --output-dir custom_directory \
    --rtos caiso ercot nyiso
```

### Command Line Arguments

| Argument | Required | Description | Default |
|----------|----------|-------------|---------|
| `--year` | Yes | Year to download data for | - |
| `--api-key` | No* | GridStatus.io API key | Uses `GRIDSTATUS_API_KEY` env var |
| `--output-dir` | No | Output directory for CSV files | `gridstatus_price` |
| `--rtos` | No | Specific RTOs to download | All RTOs |

*Required unless `GRIDSTATUS_API_KEY` environment variable is set

### RTO-Specific Location Configuration

The script uses carefully selected representative locations for each RTO:

#### CAISO (California)
- **Locations**: NP-15, SP-15, ZP-26 trading hub zones
- **Method**: Average of three major trading hubs

#### ERCOT (Texas)
- **Location**: Hub Average (HB_HUBAVG)
- **Method**: Uses pre-calculated hub average from gridstatus.io

#### ISONE (New England)
- **Locations**: Internal Hub + 8 load zones (CT, ME, NH, RI, VT, SEMA, WCMA, NEMA/Boston)
- **Method**: Average across hub and major load zones

#### MISO (Midwest)
- **Locations**: 8 regional hubs (Arkansas, Illinois, Indiana, Louisiana, Michigan, Minnesota, Mississippi, Texas)
- **Method**: Average of regional generation hubs

#### NYISO (New York)
- **Locations**: 11 load zones (A through K: West, Genesee, Central, North, Mohawk Valley, Capital, Hudson Valley, Millwood, Dunwoodie, NYC, Long Island)
- **Method**: Average across all load zones

#### PJM (Mid-Atlantic)
- **Locations**: 19 generation hubs covering all major utility territories
- **Method**: Average of utility-specific generation hubs

#### SPP (Southwest)
- **Locations**: North Hub and South Hub
- **Method**: Average of two major trading hubs

### Output Format

Each CSV file contains:
- **Header**: 4 lines of metadata describing the data source and methodology
- **Columns**:
  - UTC Timestamp (Interval Ending)
  - Local Timestamp (RTO-specific timezone)
  - Local Date
  - Hour Number (1-24)
  - Price ($/MWh)

### Example Output Structure
```
SPP Hourly Day-Ahead Prices ($/MWh) - Downloaded from gridstatus.io
Hourly day-ahead price data for SPP - Average of specific locations (SPPNORTH_HUB, SPPSOUTH_HUB)
Source: gridstatus.io API - Dataset: spp_lmp_day_ahead_hourly
UTC Timestamp (Interval Ending),Local Timestamp,Local Date,Hour Number,SPP Day-Ahead Price ($/MWh)
2024-01-01 00:00:00,2023-12-31 18:00:00,2023-12-31,19,24.93
2024-01-01 01:00:00,2023-12-31 19:00:00,2023-12-31,20,23.71
...
```

## Bash Script: `download_all_rto_prices.sh`

### Enhanced Features
- **Colored Output**: Visual progress indicators and status messages
- **Prerequisite Checking**: Verifies Python and required libraries
- **Automatic Installation**: Installs gridstatusio library if missing
- **Comprehensive Logging**: Timestamped logs with detailed progress
- **Summary Reports**: File sizes, line counts, and download statistics
- **Environment Variables**: Secure API key handling
- **Cross-platform**: Works on macOS and Linux
- **Error Handling**: Graceful failure handling with detailed error messages

### Usage

#### Basic Usage
```bash
./download_all_rto_prices.sh 2024
```

#### With Custom API Key
```bash
GRIDSTATUS_API_KEY=your_api_key ./download_all_rto_prices.sh 2024
```

#### With Custom Output Directory
```bash
./download_all_rto_prices.sh 2024 /path/to/output/directory
```

#### Disable Logging to File
```bash
./download_all_rto_prices.sh 2024 --no-log
```

### Script Options

| Option | Description | Default |
|--------|-------------|---------|
| `-y, --year YEAR` | Year to download data for | Current year |
| `-o, --output-dir DIR` | Output directory for CSV files | `gridstatus_price` |
| `-r, --rtos RTO_LIST` | Comma-separated list of RTOs | All RTOs |
| `-k, --api-key KEY` | GridStatus.io API key | Uses env var |
| `-l, --log-level LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `--no-log` | Disable logging to file (console only) | Logging enabled |
| `-h, --help` | Show help message | - |

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GRIDSTATUS_API_KEY` | Your gridstatus.io API key | Yes |

### Logging

The bash script creates detailed logs by default:
- **Location**: `{output_directory}/logs/`
- **Filename**: `download_rto_prices_YYYYMMDD_HHMMSS.log`
- **Content**: Timestamped progress, API responses, file operations, and summary statistics
- **Disable**: Use `--no-log` option to output only to console

### Example Log Output
```
[2024-01-15 10:30:15] Starting RTO price data download for year 2024
[2024-01-15 10:30:15] Output directory: gridstatus_price
[2024-01-15 10:30:15] Checking prerequisites...
[2024-01-15 10:30:16] ✓ Python 3.9.7 found
[2024-01-15 10:30:16] ✓ gridstatusio library found
[2024-01-15 10:30:16] Starting download process...
[2024-01-15 10:30:45] ✓ CAISO: 8,760 rows, 1.2MB
[2024-01-15 10:31:12] ✓ ERCOT: 8,760 rows, 1.1MB
...
```

## Setup and Installation

### Prerequisites
1. **Python 3.7+** with pip
2. **GridStatus.io API Key** (free registration at https://gridstatus.io)
3. **Internet connection** for API access

### Installation Steps

1. **Get API Key**:
   - Register at https://gridstatus.io
   - Copy your API key from the dashboard

2. **Set Environment Variable** (recommended):
   ```bash
   export GRIDSTATUS_API_KEY="your_api_key_here"
   ```

3. **Make Bash Script Executable**:
   ```bash
   chmod +x download_all_rto_prices.sh
   ```

4. **Install Python Dependencies** (automatic with bash script):
   ```bash
   pip install gridstatusio pandas
   ```

## Data Quality and Methodology

### Representative Location Selection
The system uses carefully selected locations that provide representative pricing for each RTO:

- **Hub-based RTOs** (ERCOT, SPP): Use official trading hubs
- **Zone-based RTOs** (CAISO, NYISO, ISONE): Average across major zones
- **Utility-based RTOs** (PJM, MISO): Average across regional/utility hubs

### Timezone Handling
Each RTO's data is converted to its local timezone:
- **Pacific**: CAISO
- **Central**: ERCOT, MISO, SPP  
- **Eastern**: ISONE, NYISO, PJM

### Data Validation
- Missing price data is skipped (not interpolated)
- Negative prices are preserved (common in renewable-heavy markets)
- Price statistics are reported for each download

## Troubleshooting

### Common Issues

#### API Key Problems
```
Error: GridStatus.io API key not found!
```
**Solution**: Set the `GRIDSTATUS_API_KEY` environment variable or use `--api-key` argument

#### Network/API Issues
```
Error downloading CAISO price data: HTTP 429 Too Many Requests
```
**Solution**: Wait a few minutes and retry. GridStatus.io has rate limits.

#### Missing Dependencies
```
ModuleNotFoundError: No module named 'gridstatusio'
```
**Solution**: Install with `pip install gridstatusio pandas` or use the bash script which auto-installs

#### Incomplete Data
```
Warning: Only 8,000 rows downloaded, expected 8,760
```
**Solution**: Check if the year is complete or if there are data gaps in the source

### Getting Help

1. **Check Logs**: Review the detailed log files in `{output_dir}/logs/`
2. **Verify API Key**: Test your API key at https://gridstatus.io
3. **Check Network**: Ensure stable internet connection
4. **Review Output**: Check CSV files for data quality issues

## Integration with Analysis Workflows

### File Compatibility
- CSV format matches EIA wholesale market data structure
- Compatible with existing price analysis scripts
- Headers provide metadata for automated processing

### Typical Workflow
1. Download price data using this system
2. Load CSV files into analysis tools (Python pandas, R, Excel)
3. Combine with demand data for price-demand correlation analysis
4. Use for wholesale market cost calculations

## Performance Notes

### Download Times
- **Single RTO**: ~30-60 seconds for full year
- **All RTOs**: ~5-10 minutes for full year
- **Factors**: Network speed, API response time, data volume

### File Sizes
- **Typical size**: ~1-2 MB per RTO per year
- **Total for all RTOs**: ~10-15 MB per year
- **Format**: Uncompressed CSV with headers

## Version History

- **v1.0**: Initial release with basic download functionality
- **v1.1**: Added specific location filtering based on EIA data structure
- **v1.2**: Enhanced bash wrapper with logging and error handling
- **v1.3**: Cross-platform compatibility and improved documentation 