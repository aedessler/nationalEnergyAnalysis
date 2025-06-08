# National Energy Analysis

## Details of Calculating These Numbers

### ERA5 temperatures
These are calculated using google servers on cocalc. The code is in /RTOavgTemp/era5-processor.py on cocalc. This program writes out one year (in monthly files).

run-era5-years.sh starts multiple years. check-complete-years.sh checks to see which years have all 12 months, and remove-empty-files.sh deletes files with small length.

The files are stored in /data on the server, so you need to rsync the data to your local machine. Once on my machine, the file concat.py combines the data into a single netCDF file.

### RTO-average temperatures
This code is in the directory '/RTO temp calc'. balancing_authority_temp.py calculates the population-weighted temperature of each region. These are stored in /weighted_temps.

Shape files are downloaded from [the EIA website](https://atlas.eia.gov/datasets/eia::rto-regions/explore)

Note that this code writes out the average population-weighted temp for all sub-regions of the RTOs, but those are not used.

### Estimating the fit between RTOs and temperature
This code is in RTO_polynomial_fit.py; it takes demand from the /demand directory and temperatures from the /weighted_temps and does the regression for each RTO. Note that you can set the degree of the polynomial. This program lets you set which year (2023, 2024) you're using for the fit and the degrees of the fit (cubic, 4th order, ...).

It saves plots in the /plots directory and writes out the fit in the polynomial_fits_RTO.json file.

The demand and price data are from [the EIA website](https://www.eia.gov/electricity/wholesalemarkets/index.php). There are bash scripts in the /demand and /price directories to download the relevant files.

### Calculating the impact of climate change
RTO_climate_change_impact.py creates the /climate_change_results folder and puts csv files into it containing average demand in baseline and current periods, as well as absolute and percent changes.

The program lets you select which fit json you're using to do the calculation.

Note: for temperatures below the minimum temp in the fit, the code replaces that temperature with the minimum temp and then uses that in the fit.

### Visualizing the changes
visualize_RTO_demand_changes.py contains code to generate plots of the change, which are stored in /climate_change_results/visualizations folder

The program lets you select which fit json you're using to do the calculation.

### Price vs. demand
To calculate the relation between price and demand, process_price_demand.py calculates the demand-weighted price and demand (daily average) and writes them into a csv file (daily_price_demand_YYYY.csv).

plot_price.ipynb contains code to plot up the relationship. It also calculates a smoothed fit to the summer data, which is stored in price_demand_smooth.csv.

### Total change in wholesale summer cost
This is calculated in calculate_total_cost_change_pwlf.ipynb.

### August plots
These are plots of Aug.-average price and demand, by hour. They show that prices spike in the afternoon/evening, when people are running their ACs. However, price maximizes around 8 pm in 2023 and 2024, suggesting that solar power is pushing the price peak to later in the evening.

### Older stuff
'/RTO sub-region calculation' contains the code and some results for the calculation where we did the analysis for each sub-region