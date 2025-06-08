import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json

# Read the demand changes data
demand_changes = pd.read_csv('demand_changes_by_zone_percent.csv')

# Read the centroids data
centroids = pd.read_csv('temperature/region_centroids.csv')

# Read the polynomial fits data to get average demand information
with open('polynomial_fits.json', 'r') as f:
    poly_fits = json.load(f)

# Create a dictionary of zone names and their average demands
zone_demands = {fit['zone_name']: fit['data_range']['avg_demand_GW'] 
                for fit in poly_fits['fits']}

# Extract annual changes and clean up the index
demand_changes['Region'] = demand_changes.iloc[:, 0]  # First column is region names
annual_changes = demand_changes[['Region', 'Annual']]

# Merge the datasets
merged_data = pd.merge(annual_changes, centroids, 
                      left_on='Region', 
                      right_on='name',  # Updated to match the actual column name
                      how='inner')

# Add average demand information
merged_data['avg_demand_GW'] = merged_data['Region'].map(zone_demands)

# Filter out zones with average demand less than 1 GW
merged_data = merged_data[merged_data['avg_demand_GW'] >= 5]

# Create the scatter plot
plt.figure(figsize=(12, 8))
sns.scatterplot(data=merged_data, 
                x='latitude',
                y='Annual',
                size='avg_demand_GW',  # Size points by average demand
                sizes=(50, 400),       # Set range of point sizes
                alpha=0.6)

# Add trend line
sns.regplot(data=merged_data,
            x='latitude',
            y='Annual',
            scatter=False,
            color='red')

# Customize the plot
plt.title('Annual Power Demand Changes vs. Latitude\n(Zones with avg. demand ≥ 5 GW)', fontsize=14)
plt.xlabel('Latitude (°N)', fontsize=12)
plt.ylabel('Annual Change in Power Demand (%)', fontsize=12)

# Add grid for better readability
plt.grid(True, linestyle='--', alpha=0.7)

# Optionally add text labels for points
for idx, row in merged_data.iterrows():
    plt.annotate(f"{row['Region']}\n({row['avg_demand_GW']:.1f} GW)", 
                (row['latitude'], row['Annual']),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8)

plt.tight_layout()
plt.savefig('lat_change.png')