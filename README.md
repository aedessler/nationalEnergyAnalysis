# National Energy-Temperature Analysis

A comprehensive analysis of climate change impacts on electricity demand and wholesale costs across major U.S. Regional Transmission Organizations (RTOs). This project combines temperature data, electricity demand modeling, and price analysis to quantify how rising temperatures affect energy markets.

## Project Overview

This analysis examines the relationship between temperature and electricity demand across seven major RTOs (CAISO, ERCOT, ISONE, MISO, NYISO, PJM, SPP) and projects the economic impacts of climate change on wholesale electricity costs.

### Key Findings
- Quantifies demand changes due to climate warming (1951-1980 baseline vs 2015-2024 recent period)
- Calculates wholesale cost impacts using price-demand relationships
- Provides seasonal and annual impact assessments by RTO
- Generates comprehensive visualizations of climate impacts

## Analysis Pipeline

### 1. Temperature Data Processing
**Location**: `RTO temp calc/` directory
- **Purpose**: Calculate population-weighted average temperatures for each RTO region
- **Input**: ERA5 reanalysis temperature data, RTO shapefiles from EIA
- **Output**: NetCDF files with daily temperature time series (`weighted_temps/`)
- **Key Script**: `balancing_authority_temp.py`

### 2. Polynomial Demand-Temperature Modeling
**Script**: `RTO_polynomial_fit.py`
- **Purpose**: Fit polynomial relationships between temperature and electricity demand
- **Features**:
  - Supports 3rd and 4th degree polynomial fits
  - Includes weekday/weekend effects
  - Handles data filtering and outlier removal
  - Generates diagnostic plots and fit statistics
- **Input**: Demand data (EIA or GridStatus), temperature data
- **Output**: JSON files with model coefficients (`polynomial_fits/`)
- **Usage**: `python RTO_polynomial_fit.py` (configure year and degree in script)

### 3. Climate Change Impact Analysis
**Script**: `RTO_climate_change_demand_impact.py`
- **Purpose**: Project demand changes using temperature-demand models
- **Analysis Periods**:
  - Historical baseline: 1951-1980
  - Recent period: 2015-2024
- **Features**:
  - Temperature clipping to model fit ranges
  - Monthly and annual impact calculations
  - Handles extrapolation warnings
- **Output**: CSV files with demand changes (`climate_change_results/`)
- **Usage**: `python RTO_climate_change_demand_impact.py` (configure parameters in script)

### 4. Impact Visualization
**Script**: `RTO_visualize_demand_changes.py`
- **Purpose**: Generate comprehensive visualizations of climate impacts
- **Outputs**:
  - Heatmaps of monthly percentage changes
  - Bar charts of annual changes by RTO
  - Seasonal pattern line charts
  - Combined multi-panel visualizations
- **Location**: `climate_change_results/visualizations_YYYY_degreeX/`
- **Usage**: `python RTO_visualize_demand_changes.py` (configure parameters in script)

## Data Sources and Downloads

### GridStatus.io Integration
The project includes a comprehensive system for downloading electricity market data from [gridstatus.io](https://gridstatus.io):

#### Price Data Download
**Scripts**: 
- `download_rto_prices_gridstatus.py` - Python download script
- `download_all_rto_prices.sh` - Bash wrapper with logging
- `README_gridstatus_price_download.md` - Detailed documentation

**Features**:
- Downloads day-ahead wholesale prices for all 7 RTOs
- Uses representative trading hubs/zones matching EIA data structure
- Proper timezone handling for each RTO
- Calculates RTO-wide averages from multiple locations
- EIA-compatible CSV output format

#### Demand Data Download  
**Scripts**:
- `download_rto_demand_gridstatus.py` - Python download script
- `download_all_rto_demand.sh` - Bash wrapper with logging
- `README_demand_download.md` - Detailed documentation

**Features**:
- Downloads actual load data using standardized GridStatus datasets
- Timezone conversion to local RTO time
- EIA-compatible format with proper headers

### Supported RTOs
- **CAISO** (California) - NP-15, SP-15, ZP-26 trading hubs
- **ERCOT** (Texas) - Hub average pricing
- **ISONE** (New England) - Internal hub + load zones
- **MISO** (Midwest) - Regional generation hubs
- **NYISO** (New York) - Load zones A through K
- **PJM** (Mid-Atlantic) - Utility generation hubs
- **SPP** (Southwest) - North and South trading hubs

## Price-Demand Analysis

### Daily Price-Demand Processing
**Script**: `process_price_demand.py`
- **Purpose**: Calculate demand-weighted daily average prices
- **Features**:
  - Matches price and demand files by RTO and year
  - Calculates demand-weighted price averages
  - Filters for complete 24-hour days
  - Converts MW to GW for consistency
- **Output**: `daily_price_demand_YYYY.csv`

### Price-Demand Relationship Modeling
**Notebook**: `plot_price.ipynb`
- **Purpose**: Analyze and model price-demand relationships
- **Features**:
  - Piecewise linear fits for price-demand curves
  - Summer data focus (high demand periods)
  - Smoothed relationship modeling
- **Output**: `price_demand_pwlf_YYYY.json` contains the demand-price fits, visualization plots

## Economic Impact Analysis

### Total Cost Change Calculation
**Script**: `calculate_total_cost_pwlf.py`
- **Purpose**: Calculate total wholesale cost impacts of climate change
- **Features**:
  - Uses polynomial demand models and piecewise linear price models
  - Analyzes summer months (June-September) when impacts are highest
  - Compares baseline (1951-1980) vs recent (2015-2024) periods
  - Provides results for multiple model configurations
- **Analysis Parameters**:
  - Years: 2023, 2024 (for model fitting)
  - Polynomial degrees: 3, 4
  - Focus: Summer wholesale cost changes
- **Output**: Comprehensive cost impact tables in billions of dollars

## File Structure

```
├── README.md                              # This file
├── RTO_polynomial_fit.py                  # Temperature-demand modeling
├── RTO_climate_change_demand_impact.py    # Climate impact analysis
├── RTO_visualize_demand_changes.py        # Impact visualization
├── process_price_demand.py                # Price-demand data processing
├── calculate_total_cost_pwlf.py           # Economic impact calculation
├── download_rto_prices_gridstatus.py      # Price data download
├── download_rto_demand_gridstatus.py      # Demand data download
├── download_all_rto_prices.sh             # Price download wrapper
├── download_all_rto_demand.sh             # Demand download wrapper
├── plot_price.ipynb                       # Price analysis notebook
├── polynomial_fits/                       # Model coefficients
│   ├── polynomial_fits_RTO_2023_degree3.json
│   ├── polynomial_fits_RTO_2023_degree4.json
│   ├── polynomial_fits_RTO_2024_degree3.json
│   └── polynomial_fits_RTO_2024_degree4.json
├── climate_change_results/                # Impact analysis results
│   ├── rto_demand_changes_percent_YYYY_degreeX.csv
│   ├── rto_demand_changes_absolute_YYYY_degreeX.csv
│   ├── rto_demand_baseline_YYYY_degreeX.csv
│   ├── rto_demand_current_YYYY_degreeX.csv
│   └── visualizations_YYYY_degreeX/       # Impact visualizations
├── gridstatus_price/                      # Price data and analysis
│   ├── *_price_day_ahead_hr_YYYY.csv      # Hourly price data
│   ├── daily_price_demand_YYYY.csv        # Daily aggregated data
│   └── price_demand_pwlf_YYYY.json        # Price-demand models
├── gridstatus_demand/                     # Demand data
│   └── *_load_act_hr_YYYY.csv             # Hourly demand data
├── plots/                                 # Analysis visualizations
├── RTO temp calc/                         # Temperature processing
│   └── weighted_temps/                    # RTO temperature data
└── era5/                                  # Raw temperature data
```

## Requirements

### Python Dependencies
```python
pandas
numpy
xarray
scikit-learn
matplotlib
seaborn
gridstatusio  # For data downloads
```

### External Data
- ERA5 reanalysis temperature data
- RTO shapefiles from EIA
- GridStatus.io API key (for data downloads)

## Usage Examples

### Run Complete Analysis Pipeline
```bash
# 1. Download data (requires API key)
python download_rto_prices_gridstatus.py --year 2024 --api-key YOUR_KEY
python download_rto_demand_gridstatus.py --year 2024 --api-key YOUR_KEY

# 2. Fit temperature-demand models
python RTO_polynomial_fit.py  # Configure year/degree in script

# 3. Calculate climate impacts
python RTO_climate_change_demand_impact.py  # Configure parameters in script

# 4. Generate visualizations
python RTO_visualize_demand_changes.py  # Configure parameters in script

# 5. Process price-demand relationships
python process_price_demand.py

# 6. Calculate economic impacts
python calculate_total_cost_pwlf.py
```

### Key Configuration Parameters
Most scripts use internal configuration. Key parameters to modify:
- **Year**: 2023 or 2024 (for model fitting)
- **Polynomial degree**: 3 or 4
- **Analysis periods**: Historical (1951-1980) vs Recent (2015-2024)
- **Summer months**: June-September (6,7,8,9)

## Analysis Results

The analysis produces several types of outputs:

1. **Demand Impact Tables**: Percentage and absolute changes in electricity demand
2. **Economic Impact Analysis**: Wholesale cost changes in billions of dollars
3. **Seasonal Patterns**: Monthly breakdown of climate impacts
4. **Visualizations**: Heatmaps, bar charts, and trend analysis
5. **Model Diagnostics**: Fit statistics and diagnostic plots

## Documentation

- `README_gridstatus_price_download.md` - Detailed price download documentation
- `README_demand_download.md` - Detailed demand download documentation
- Individual script docstrings provide implementation details

## Notes

- Temperature data requires significant preprocessing (see ERA5 processing notes in original README)
- Model fits are specific to the training year and polynomial degree
- Economic analysis focuses on summer months when climate impacts are most pronounced
- All monetary values are in nominal dollars for the analysis year