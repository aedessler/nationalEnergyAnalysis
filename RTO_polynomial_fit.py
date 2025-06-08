import pandas as pd
import xarray as xr
import numpy as np
from sklearn.linear_model import LinearRegression
import json
import warnings
import matplotlib.pyplot as plt
import os

# Filter out the FutureWarning about month end resampling
warnings.filterwarnings('ignore', category=FutureWarning, message="'M' is deprecated")

def find_total_column(df):
    """Find the column name that contains 'total' (case insensitive)."""
    for col in df.columns:
        if 'total' in col.lower():
            return col
    raise ValueError("No column with 'total' in its name found")

def generate_x(X, date, max_degree=4):
    """
    Generate regressors for the regression of demand vs. temperature
    
    Parameters:
    -----------
    X : array-like
        Temperature values
    date : pd.DatetimeIndex
        Dates corresponding to the temperature values
    max_degree : int, default=4
        Maximum polynomial degree to use in the fit
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with polynomial terms up to max_degree
    """
    data = pd.DataFrame({'Temperature': X}, index=date)
    
    # Add polynomial terms up to max_degree
    for degree in range(2, max_degree + 1):
        data[f'Temperature^{degree}'] = X**degree
    
    # Make categorical variable for weekday vs. weekend
    data['category'] = (date.weekday < 5).astype(int)  # Weekday = 1, Weekend = 0
    
    return data

def fit_zone(demand_file, temp_file, max_degree=4):
    """
    Fit temperature-demand relationship for a single zone and save coefficients
    
    Parameters:
    -----------
    demand_file : str
        Path to the demand data file
    temp_file : str
        Path to the temperature data file
    max_degree : int, default=4
        Maximum polynomial degree to use in the fit
    """
    print(f"\nFitting zone based on demand file: {os.path.basename(demand_file)}")
    print(f"Using polynomial degree: {max_degree}")
    
    # Read demand data
    demand_df = pd.read_csv(demand_file, skiprows=3)
    demand_df['datetime'] = pd.to_datetime(demand_df.iloc[:,1])
    demand_df.set_index('datetime', inplace=True)
    
    # Print columns for debugging
    print(f"Available columns in demand file: {demand_df.columns.tolist()}")
    
    # Find the column with 'total' in its name
    total_column = find_total_column(demand_df)
    print(f"Using demand column: '{total_column}'")
    
    # Get demand for the region and convert to GW
    region_demand = demand_df[total_column]/1e3
    
    # Calculate daily average demand
    daily_demand = region_demand.resample('D').mean()
    
    # Read temperature data
    print(f"Reading temperature file: {temp_file}")
    temp_ds = xr.open_dataset(temp_file)
    
    temp_series = temp_ds.t2m.to_series()
                
    # Extract RTO name from demand file (part before first underscore)
    rto_name = os.path.basename(demand_file).split('_')[0].upper()
    
    # Align the dates
    common_dates = daily_demand.index.intersection(temp_series.index)
    if len(common_dates) == 0:
        raise ValueError(f"No common dates between demand and temperature data for {rto_name}")
        
    daily_demand = daily_demand[common_dates]
    daily_temp = temp_series[common_dates]
    
    # Remove any NaN values
    valid_mask = ~(np.isnan(daily_demand) | np.isnan(daily_temp))
    daily_demand = daily_demand[valid_mask]
    daily_temp = daily_temp[valid_mask]
    
    # Remove zero demand days
    nonzero_mask = (daily_demand > 0)
    daily_demand = daily_demand[nonzero_mask]
    daily_temp = daily_temp[nonzero_mask]
    
    # For PJM data, remove days with demand < 30 GW
    if os.path.basename(demand_file).lower().startswith('pjm'):
        pjm_filter = (daily_demand >= 40)
        daily_demand = daily_demand[pjm_filter]
        daily_temp = daily_temp[pjm_filter]
    
    # For ERCOT data, remove days with demand > 80 GW
    if os.path.basename(demand_file).lower().startswith('ercot'):
        ercot_filter = (daily_demand <= 80)
        daily_demand = daily_demand[ercot_filter]
        daily_temp = daily_temp[ercot_filter]
    
    if len(daily_demand) < 30:
        raise ValueError(f"Insufficient data: only {len(daily_demand)} valid days")
    
    print(f"Fitting model on {len(daily_demand)} days of data")
    
    # Train model
    X = daily_temp.values
    data = generate_x(X, daily_demand.index, max_degree)
    y = daily_demand.values
    model = LinearRegression().fit(data, y)
    
    # Get predictions using actual weekday/weekend categories
    y_pred = model.predict(data)
    
    # Calculate fit statistics
    rmse = np.sqrt(np.mean((y - y_pred)**2))
    r2 = model.score(data, y)
    
    # Create two-panel plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Add overall title with zone info
    fig.suptitle(f'Temperature-Demand Relationship for {rto_name} (Degree {max_degree} Polynomial)', 
                 fontsize=14, y=1.05)
    
    # Get min and max temperature values and extend by 5 degrees
    temp_min = np.min(X) - 5
    temp_max = np.max(X) + 5
    
    # Create evenly spaced temperature values for smooth curve plotting
    # Use 200 points for smooth curve
    X_evenly_spaced = np.linspace(temp_min, temp_max, 200)
    
    # Create a fake DatetimeIndex for these evenly spaced points
    # We'll use the same weekday/weekend distribution as the original data
    fake_dates = pd.date_range(start=daily_demand.index[0], periods=len(X_evenly_spaced))
    
    # Generate features for evenly spaced temperature values
    data_evenly_spaced = generate_x(X_evenly_spaced, fake_dates, max_degree)
    
    # Set category to average weekday/weekend effect for smooth curve
    data_evenly_spaced['category'] = 5/7  # Average between weekday and weekend
    
    # Predict demand using evenly spaced temperature values
    y_pred_evenly_spaced = model.predict(data_evenly_spaced)
    
    # Left Panel: Temperature vs Demand
    ax1.scatter(X, y, alpha=0.5, label='Data')
    ax1.plot(X_evenly_spaced, y_pred_evenly_spaced, color='k', ls='--', lw=2, label='Fit')
    
    # Add vertical lines to show original data range
    ax1.axvline(x=np.min(X), color='r', linestyle=':', alpha=0.5, label='Data Range')
    ax1.axvline(x=np.max(X), color='r', linestyle=':', alpha=0.5)
    
    ax1.set_title('Temperature vs Demand')
    ax1.set_xlabel('Daily Avg. Temperature (°C)')
    ax1.set_ylabel('Daily Avg. Demand (GW)')
    ax1.grid(True)
    ax1.legend()
    
    # Right Panel: Predicted vs Actual Demand
    ax2.scatter(y, y_pred, alpha=0.5)
    ax2.plot([min(y), max(y)], [min(y), max(y)], 'k--', lw=2)
    ax2.set_title('Predicted vs Actual Demand')
    ax2.set_xlabel('Actual Daily Avg. Demand (GW)')
    ax2.set_ylabel('Predicted Daily Avg. Demand (GW)')
    ax2.grid(True)
    
    # Add RMSE as text box
    textstr = f'RMSE: {rmse:.1f} GW'
    ax2.text(0.05, 0.95, textstr, transform=ax2.transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.5))
    
    # Add weekday effect size as text box
    weekday_effect_size = model.coef_[-1]  # Last coefficient corresponds to the weekday/weekend category
    textstr2 = f'Weekday Effect: {weekday_effect_size:.2f} GW'
    ax1.text(0.05, 0.95, textstr2, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.5))
    
    # Create plots directory if it doesn't exist
    os.makedirs('plots', exist_ok=True)
    
    plt.tight_layout()
    plt.savefig(f'plots/temp_vs_demand_fit_{rto_name.lower()}_degree{max_degree}.pdf', 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\nPlot saved as plots/temp_vs_demand_fit_{rto_name.lower()}_degree{max_degree}.pdf")
    print(f"RMSE: {rmse:.1f} GW")
    print(f"Weekday Effect: {weekday_effect_size:.2f} GW")
    print(f"Temp range in data: {np.min(X):.1f}°C to {np.max(X):.1f}°C")
    
    # Create coefficient dictionary with dynamic entries
    coef_dict = {
        'rto': rto_name,
        'fit_details': {
            'max_degree': max_degree
        },
        'coefficients': {
            'constant': float(model.intercept_),
            'temperature': float(model.coef_[0]),
        }
    }
    
    # Add the polynomial terms based on max_degree
    for degree in range(2, max_degree + 1):
        coef_dict['coefficients'][f'temperature^{degree}'] = float(model.coef_[degree - 1])
        
    # Add weekday effect (always the last coefficient)
    coef_dict['coefficients']['weekday_effect'] = float(model.coef_[-1])
    
    # Add fit statistics and data range
    coef_dict.update({
        'fit_statistics': {
            'rmse_GW': float(rmse),
            'r2': float(r2),
            'n_days': int(len(daily_demand))
        },
        'data_range': {
            'start_date': daily_demand.index.min().strftime('%Y-%m-%d'),
            'end_date': daily_demand.index.max().strftime('%Y-%m-%d'),
            'min_temp_C': float(daily_temp.min()),
            'max_temp_C': float(daily_temp.max()),
            'avg_demand_GW': float(daily_demand.mean()),
            'max_demand_GW': float(daily_demand.max())
        }
    })
    
    return coef_dict

def main(max_degree=4):
    """
    Run polynomial fits with hardcoded file mappings.
    
    Parameters:
    -----------
    max_degree : int, default=4
        Maximum polynomial degree to use in the fits
    """
    print(f"Starting polynomial fits with max degree: {max_degree}")
    
    # Hardcoded directory paths
    demand_dir = 'demand'
    weighted_temps_dir = 'RTO temp calc/weighted_temps'
    
    print(f"\nUsing demand directory: {demand_dir}")
    print(f"Using temperature directory: {weighted_temps_dir}")
    
    # Initialize results list
    results = []
    errors = []
    
    # Process each file pair from the mapping
    for demand_filename, temp_filename in FILE_MAPPING.items():

        demand_file = os.path.join(demand_dir, demand_filename)
        temp_file = os.path.join(weighted_temps_dir, temp_filename)
        
        print(f"\nProcessing file pair:")
        print(f"  Demand: {demand_file}")
        print(f"  Temperature: {temp_file}")
        
        # Check if files exist
        if not os.path.exists(demand_file):
            raise ValueError(f"Demand file does not exist: {demand_file}")
        if not os.path.exists(temp_file):
            raise ValueError(f"Temperature file does not exist: {temp_file}")
        
        try:
            # Fit model for this zone
            coef_dict = fit_zone(demand_file, temp_file, max_degree=max_degree)
            results.append(coef_dict)
            print(f"Successfully fit model for {os.path.basename(demand_file)}")
        except Exception as e:
            error_msg = f"Error fitting model for {demand_filename}: {str(e)}"
            print(f"ERROR: {error_msg}")
            errors.append(error_msg)
                
    # Save results to JSON file
    output_file = f'polynomial_fits_RTO_{year}_degree{max_degree}.json'
    with open(output_file, 'w') as f:
        json.dump({
            'fits': results,
            'errors': errors,
            'metadata': {
                'max_degree': max_degree,
                'n_zones_total': len(FILE_MAPPING),
                'n_zones_successful': len(results),
                'n_zones_failed': len(errors)
            }
        }, f, indent=2)
    
    print(f"\nAnalysis complete!")
    print(f"Successfully fit {len(results)} zones with polynomial degree {max_degree}")
    print(f"Results saved to {output_file}")
    
    if errors:
        print("\nThe following errors occurred:")
        for error in errors:
            print(f"- {error}")

# Hard-coded mapping between demand and temperature files
year = 2024 ## which year to use for the demand & temp data
FILE_MAPPING = {
    f'caiso_load_act_hr_{year}.csv': 'CALIFORNIA_INDEPENDENT_SYSTEM_OPERATOR_weighted_temp.nc',
    f'ercot_load_act_hr_{year}.csv': 'ELECTRIC_RELIABILITY_COUNCIL_OF_TEXAS,_INC._weighted_temp.nc',
    f'isone_load_actr_hr_{year}.csv': 'ISO_NEW_ENGLAND_INC._weighted_temp.nc',
    f'miso_load_act_hr_{year}.csv': 'MIDCONTINENT_INDEPENDENT_TRANSMISSION_SYSTEM_OPERATOR,_INC.._weighted_temp.nc',
    f'nyiso_load_act_hr_{year}.csv': 'NEW_YORK_INDEPENDENT_SYSTEM_OPERATOR_weighted_temp.nc',
    f'pjm_load_act_hr_{year}.csv': 'PJM_INTERCONNECTION,_LLC_weighted_temp.nc',
    f'spp_load_act_hr_{year}.csv': 'SOUTHWEST_POWER_POOL_weighted_temp.nc'
}

# Run the main function with the specified degree
main(max_degree=3) 