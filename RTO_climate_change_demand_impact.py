import pandas as pd
import xarray as xr
import numpy as np
import json
import sys
import os
import warnings
from pathlib import Path

# Filter out the FutureWarning about month end resampling
warnings.filterwarnings('ignore', category=FutureWarning, message="'M' is deprecated")

# Define mapping between RTO names and temperature files
RTO_TEMP_MAPPING = {
    'CAISO': 'CALIFORNIA_INDEPENDENT_SYSTEM_OPERATOR_weighted_temp.nc',
    'ERCOT': 'ELECTRIC_RELIABILITY_COUNCIL_OF_TEXAS,_INC._weighted_temp.nc',
    'ISONE': 'ISO_NEW_ENGLAND_INC._weighted_temp.nc',
    'MISO': 'MIDCONTINENT_INDEPENDENT_TRANSMISSION_SYSTEM_OPERATOR,_INC.._weighted_temp.nc',
    'NYISO': 'NEW_YORK_INDEPENDENT_SYSTEM_OPERATOR_weighted_temp.nc',
    'PJM': 'PJM_INTERCONNECTION,_LLC_weighted_temp.nc',
    'SPP': 'SOUTHWEST_POWER_POOL_weighted_temp.nc'
}

def clip_temperatures(temps, min_temp, max_temp):
    """Clip temperature values to be within the range of the fit data.
    
    Args:
        temps: Array of temperature values
        min_temp: Minimum temperature allowed (from fit data)
        max_temp: Maximum temperature allowed (from fit data)
        
    Returns:
        Array of clipped temperature values
    """
    # Convert to numpy array if it's not already
    temps_array = np.array(temps)
    
    # Create a copy to avoid modifying the original array
    clipped_temps = temps_array.copy()
    
    # Check for temperatures outside the fit range
    below_min = temps_array < min_temp
    above_max = temps_array > max_temp
    
    # Count how many temperatures are outside the range
    num_below = np.sum(below_min)
    num_above = np.sum(above_max)
    
    # Clip temperatures to the min/max range
    if num_below > 0:
        print(f"Warning: {num_below} temperature values below minimum fit temperature ({min_temp:.2f}°C). Clipping to minimum.")
        clipped_temps[below_min] = min_temp
        
    if num_above > 0:
        print(f"Warning: {num_above} temperature values above maximum fit temperature ({max_temp:.2f}°C). Clipping to maximum.")
        clipped_temps[above_max] = max_temp
        
    return clipped_temps

def generate_x(X, date, degree_of_fit):
    """Generate regressors for the regression of demand vs. temperature"""
    data = pd.DataFrame({'Constant': 1}, index=date)
    
    # Add polynomial terms up to the specified degree
    for i in range(1, degree_of_fit + 1):
        data[f'Temperature^{i}'] = X**i

    # Make categorical variable for weekday vs. weekend
    data['category'] = (date.weekday < 5).astype(int)  # Weekday = 1, Weekend = 0
    
    return data

def predict_demand(X, dates, coefficients, degree_of_fit):
    """Predict demand using pre-computed polynomial coefficients"""
    data = generate_x(X, dates, degree_of_fit)
    
    # Start with constant term
    y_pred = coefficients['constant']
    
    # Add polynomial terms up to the specified degree
    for i in range(1, degree_of_fit + 1):
        coef_key = 'temperature' if i == 1 else f'temperature^{i}'
        if coef_key in coefficients:
            y_pred += coefficients[coef_key] * data[f'Temperature^{i}']
    
    # Add weekday effect
    y_pred += coefficients['weekday_effect'] * data['category']
    
    return y_pred

def analyze_rto(rto_name, temp_file_path, polynomial_fit, degree_of_fit):
    """Analyze temperature-demand relationship for a single RTO using pre-computed fits"""
    print(f"\nAnalyzing RTO: {rto_name}")
    
    # Extract coefficients for the RTO
    rto_coefficients = polynomial_fit['coefficients']
    print(f"Weekday Effect: {rto_coefficients['weekday_effect']:.2f} GW")
    
    # Extract temperature range from the fit data - FIX: Access from the nested data_range field
    min_temp = polynomial_fit.get('data_range', {}).get('min_temp_C', None)
    max_temp = 50
    
    # Check if temperature range is available in the fit data
    if min_temp is None:
        print("Warning: Temperature range not found in fit data. Extrapolation may occur.")
        # Use reasonable defaults if not available
        min_temp = -30.0  # Very cold temperature
    else:
        print(f"Temperature fit range: {min_temp:.2f}°C to {max_temp:.2f}°C")
    
    # Load temperature data
    try:
        temp_ds = xr.open_dataset(temp_file_path)
        print(f"Loaded temperature data from {temp_file_path}")
    except Exception as e:
        print(f"Error opening temperature file: {str(e)}")
        raise
    
    # Extract temperature variable (assuming it's named 'temperature')
    temp_var_name = 't2m' 
    temp_data = temp_ds[temp_var_name]
    
    # Function to predict demand for a given time period
    def predict_period_demand(start_year, end_year):
        print(f"\nPredicting demand for period {start_year}-{end_year}")
        
        # Get temperature data for the period
        try:
            period_temp = temp_data.sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))
            
            if len(period_temp) == 0:
                raise ValueError(f"No temperature data found for period {start_year}-{end_year}")
                
            # Convert to Celsius if needed (ERA5 data is in Kelvin)
            if period_temp.mean() > 100:  # Simple check if temperature is in Kelvin
                print("Converting temperature from Kelvin to Celsius")
                period_temp = period_temp - 273.15
                
            # Resample to daily means
            daily_period_temp = period_temp.resample(time='D').mean()
            
            # Get dates for the period
            dates = daily_period_temp.time.to_index()
            
            # Clip temperatures to be within the fit range
            clipped_temps = clip_temperatures(daily_period_temp.values, min_temp, max_temp)
            
            # Get predictions using pre-computed coefficients (with clipped temperatures)
            predictions = predict_demand(clipped_temps, dates, rto_coefficients, degree_of_fit)
            
            # Create series with datetime index
            pred_series = pd.Series(predictions, index=dates)
            
            # Calculate monthly averages
            monthly_means = pred_series.resample('ME').mean()

            # Group by month and calculate mean across years
            monthly_results = monthly_means.groupby(monthly_means.index.month).mean()
            
            return monthly_results
        
        except Exception as e:
            print(f"Error predicting demand for period {start_year}-{end_year}: {str(e)}")
            raise
    
    # Calculate average demand for historical and recent periods
    historical_period = (1951, 1980)  # Historical baseline
    recent_period = (2015, 2024)      # Recent period
    
    try:
        demand_historical = predict_period_demand(*historical_period)
        demand_recent = predict_period_demand(*recent_period)
        
        # Calculate changes
        changes = demand_recent - demand_historical
        print("\nAnalysis complete for this RTO")
        
        return changes, demand_historical, demand_recent
    
    except Exception as e:
        print(f"Error in analysis: {str(e)}")
        raise

def main(degree_of_fit, year):
    print("Starting RTO climate change demand impact analysis...")
    print(f"Using polynomial fit of degree {degree_of_fit}")
    
    # Define file paths
    # Adjust these paths based on where your files are actually located
    poly_fits_path = f'polynomial_fits_RTO_{year}_degree{degree_of_fit}.json'
    temp_dir = 'RTO calc temps/weighted_temps'
        
    if not os.path.exists(temp_dir):
        # Try alternative locations
        alternate_temp_dir = '/Users/adessler/Documents/CopyFolder/national energy-temp analysis/RTO temp calc/weighted_temps'
        if os.path.exists(alternate_temp_dir):
            temp_dir = alternate_temp_dir
            print(f"Using temperature data from: {temp_dir}")
    
    # Read polynomial fits
    try:
        with open(poly_fits_path, 'r') as f:
            polynomial_fits = json.load(f)
        print(f"Loaded polynomial fits for RTOs")
    except Exception as e:
        print(f"Error reading polynomial fits file: {str(e)}")
        sys.exit(1)
    
    # Initialize results dictionaries
    results = {}
    baseline_results = {}
    current_results = {}
    annual_changes = {}
    errors = []
    
    # Analyze each RTO
    for rto_name, temp_filename in RTO_TEMP_MAPPING.items():
        temp_file_path = os.path.join(temp_dir, temp_filename)
        
        # Find the matching polynomial fit
        rto_fit = None
        for fit in polynomial_fits['fits']:
            if fit['rto'] == rto_name:
                rto_fit = fit
                break
        
        if rto_fit is None:
            error_msg = f"No polynomial fit found for RTO {rto_name}"
            print(error_msg)
            errors.append(error_msg)
            continue
        
        # Check if temperature file exists
        if not os.path.exists(temp_file_path):
            error_msg = f"Temperature file not found: {temp_file_path}"
            print(error_msg)
            errors.append(error_msg)
            continue
        
        try:
            changes, baseline, current = analyze_rto(rto_name, temp_file_path, rto_fit, degree_of_fit)
            results[rto_name] = changes
            baseline_results[rto_name] = baseline
            current_results[rto_name] = current
            
            # Calculate annual averages
            annual_baseline = baseline.mean()
            annual_current = current.mean()
            annual_change = changes.mean()
            annual_changes[rto_name] = annual_change
            
        except Exception as e:
            error_msg = f"Error analyzing RTO {rto_name}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
            continue
    
    if not results:
        print("\nNo results were generated. Check the errors above.")
        sys.exit(1)
        
    # Create output directory if it doesn't exist
    # Use the directory where the polynomial_fits file was found
    output_dir_parent = os.path.dirname(poly_fits_path)
    output_dir = os.path.join(output_dir_parent, f"climate_change_results")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Convert results to DataFrames
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Absolute changes
    results_df = pd.DataFrame(results).T
    results_df.columns = month_names
    results_df['Annual'] = pd.Series(annual_changes)
    
    # Baseline and current values
    baseline_df = pd.DataFrame(baseline_results).T
    baseline_df.columns = month_names
    baseline_df['Annual'] = baseline_df.mean(axis=1)
    
    current_df = pd.DataFrame(current_results).T
    current_df.columns = month_names
    current_df['Annual'] = current_df.mean(axis=1)
    
    # Calculate percent changes
    percent_changes_df = ((current_df - baseline_df) / baseline_df * 100).round(1)
    
    # Save results with year and degree in filenames
    results_df.to_csv(os.path.join(output_dir, f'rto_demand_changes_absolute_{year}_degree{degree_of_fit}.csv'))
    percent_changes_df.to_csv(os.path.join(output_dir, f'rto_demand_changes_percent_{year}_degree{degree_of_fit}.csv'))
    baseline_df.to_csv(os.path.join(output_dir, f'rto_demand_baseline_{year}_degree{degree_of_fit}.csv'))
    current_df.to_csv(os.path.join(output_dir, f'rto_demand_current_{year}_degree{degree_of_fit}.csv'))
    
    # Save results as JSON for easier visualization
    results_json = {
        'rtos': list(results.keys()),
        'months': month_names,
        'absolute_changes': {rto: results[rto].tolist() for rto in results},
        'percent_changes': {rto: percent_changes_df.loc[rto, month_names].tolist() for rto in results},
        'baseline': {rto: baseline_results[rto].tolist() for rto in baseline_results},
        'current': {rto: current_results[rto].tolist() for rto in current_results},
        'annual_changes': annual_changes,
        'metadata': {
            'year': year,
            'degree_of_fit': degree_of_fit
        }
    }
    
    with open(os.path.join(output_dir, f'rto_climate_change_impact_results_{year}_degree{degree_of_fit}.json'), 'w') as f:
        json.dump(results_json, f, indent=2)
    
    print("\nAnalysis complete!")
    print(f"Results saved to {output_dir}/")
    print(f"Successfully analyzed {len(results)} RTOs")
    
    if errors:
        print("\nThe following errors occurred:")
        for error in errors:
            print(f"- {error}")

if __name__ == "__main__":
    degree_of_fit = 4 ## which degree of polynomial fit to use
    year = 2023 ## which year to use for the demand & temp data in the polynomial fit
    main(degree_of_fit, year) 