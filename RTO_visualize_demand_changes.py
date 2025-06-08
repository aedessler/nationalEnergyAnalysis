import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
from pathlib import Path

def main(year, degree_of_fit):
    print(f"Visualizing RTO demand percentage changes for year {year} and polynomial degree {degree_of_fit}...")
    
    # Determine the path to the CSV file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    # Try to find the results directory
    possible_paths = [
        os.path.join(script_dir, f"climate_change_results", f"rto_demand_changes_percent_{year}_degree{degree_of_fit}.csv"),
        os.path.join(parent_dir, f"climate_change_results", f"rto_demand_changes_percent_{year}_degree{degree_of_fit}.csv"),
    ]
    
    # Find the first valid path
    data_path = None
    for path in possible_paths:
        if os.path.exists(path):
            data_path = path
            break
    
    if not data_path:
        print(f"Could not find rto_demand_changes_percent_{year}_degree{degree_of_fit}.csv. Please specify the correct path.")
        return
    
    print(f"Loading data from: {data_path}")
    
    # Read the CSV data
    df = pd.read_csv(data_path, index_col=0)
    
    # Extract month columns (excluding 'Annual' column if it exists)
    month_cols = [col for col in df.columns if col != 'Annual']
    
    # Create output directory for visualizations
    output_dir = os.path.join(os.path.dirname(data_path), f"visualizations_{year}_degree{degree_of_fit}")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Create a heatmap of monthly percentage changes
    create_heatmap(df, month_cols, output_dir, year, degree_of_fit)
    
    # 2. Create a bar chart of annual changes
    if 'Annual' in df.columns:
        create_annual_bar_chart(df, output_dir, year, degree_of_fit)
    
    # 3. Create line chart showing seasonal patterns for each RTO
    create_seasonal_line_chart(df, month_cols, output_dir, year, degree_of_fit)
    
    # 4. Create a combined visualization
    create_combined_visualization(df, month_cols, output_dir, year, degree_of_fit)
    
    print(f"Visualizations saved to: {output_dir}")

def create_heatmap(df, month_cols, output_dir, year, degree_of_fit):
    """Create a heatmap of monthly percentage changes across RTOs"""
    plt.figure(figsize=(12, 8))
    
    # Create heatmap
    heatmap_data = df[month_cols].copy()
    
    # Set up the heatmap with a diverging colormap
    ax = sns.heatmap(heatmap_data, 
                     cmap="RdBu_r",
                     center=0,
                     annot=True, 
                     fmt=".1f", 
                     linewidths=0.5,
                     cbar_kws={'label': 'Percent Change (%)'})
    
    # Improve the appearance
    plt.title(f'Percentage Change in Electricity Demand Due to Climate Change by RTO and Month\n(Year: {year}, Polynomial Degree: {degree_of_fit})', fontsize=14)
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Regional Transmission Organization (RTO)', fontsize=12)
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(os.path.join(output_dir, f'rto_demand_heatmap_{year}_degree{degree_of_fit}.png'), dpi=300, bbox_inches='tight')
    plt.close()

def create_annual_bar_chart(df, output_dir, year, degree_of_fit):
    """Create a horizontal bar chart of annual percentage changes"""
    plt.figure(figsize=(10, 8))
    
    # Sort by Annual change value
    sorted_data = df.sort_values('Annual')
    
    # Create a horizontal bar chart
    bars = plt.barh(sorted_data.index, sorted_data['Annual'], color=plt.cm.RdBu_r(np.interp(sorted_data['Annual'], 
                                                                               [-max(abs(sorted_data['Annual'])), max(abs(sorted_data['Annual']))], 
                                                                               [0, 1])))
    
    # Add data labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        label_x_pos = width if width >= 0 else width - 0.5
        plt.text(label_x_pos, bar.get_y() + bar.get_height()/2, f'{width:.1f}%', 
                 va='center', ha='left' if width >= 0 else 'right', fontweight='bold')
    
    # Add a vertical line at x=0
    plt.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    
    # Improve the appearance
    plt.title(f'Annual Percentage Change in Electricity Demand Due to Climate Change by RTO\n(Year: {year}, Polynomial Degree: {degree_of_fit})', fontsize=14)
    plt.xlabel('Percent Change (%)', fontsize=12)
    plt.ylabel('Regional Transmission Organization (RTO)', fontsize=12)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(os.path.join(output_dir, f'rto_annual_changes_bar_{year}_degree{degree_of_fit}.png'), dpi=300, bbox_inches='tight')
    plt.close()

def create_seasonal_line_chart(df, month_cols, output_dir, year, degree_of_fit):
    """Create a line chart showing seasonal patterns for each RTO"""
    plt.figure(figsize=(12, 8))
    
    # Plot each RTO as a line
    for rto in df.index:
        plt.plot(month_cols, df.loc[rto, month_cols], marker='o', linewidth=2, label=rto)
    
    # Add a horizontal line at y=0
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # Improve the appearance
    plt.title(f'Seasonal Pattern of Electricity Demand Changes Due to Climate Change by RTO\n(Year: {year}, Polynomial Degree: {degree_of_fit})', fontsize=14)
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Percent Change (%)', fontsize=12)
    plt.grid(linestyle='--', alpha=0.7)
    plt.legend(title='RTO', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(os.path.join(output_dir, f'rto_seasonal_changes_line_{year}_degree{degree_of_fit}.png'), dpi=300, bbox_inches='tight')
    plt.close()

def create_combined_visualization(df, month_cols, output_dir, year, degree_of_fit):
    """Create a combined visualization with multiple subplots"""
    fig = plt.figure(figsize=(15, 10))
    
    # Create a 2x2 grid of subplots with more space between them
    gs = fig.add_gridspec(2, 2, hspace=0.4, wspace=0.4)
    
    # 1. Heatmap in top-left
    ax1 = fig.add_subplot(gs[0, 0])
    sns.heatmap(df[month_cols], cmap="RdBu_r", center=0, annot=False, 
                cbar_kws={'label': 'Percent Change (%)'}, ax=ax1)
    ax1.set_title('Monthly Percentage Changes Heatmap')
    ax1.set_xlabel('Month')
    ax1.set_ylabel('RTO')
    
    # 2. Annual bar chart in top-right
    ax2 = fig.add_subplot(gs[0, 1])
    if 'Annual' in df.columns:
        # Sort by Annual value
        sorted_idx = df['Annual'].sort_values().index
        y_pos = range(len(sorted_idx))
        
        # Create a horizontal bar chart
        colors = plt.cm.RdBu_r(np.interp(df.loc[sorted_idx, 'Annual'], 
                             [-max(abs(df['Annual'])), max(abs(df['Annual']))], 
                             [0, 1]))
        bars = ax2.barh(y_pos, df.loc[sorted_idx, 'Annual'], color=colors)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(sorted_idx)
        ax2.axvline(x=0, color='black', linestyle='-', alpha=0.3)
        ax2.set_title('Annual Percentage Changes')
        ax2.set_xlabel('Percent Change (%)')
        
        # Add data labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            label_x_pos = width if width >= 0 else width - 0.5
            ax2.text(label_x_pos, bar.get_y() + bar.get_height()/2, f'{width:.1f}%', 
                     va='center', ha='left' if width >= 0 else 'right', fontweight='bold')
    
    # 3. Seasonal line chart at bottom
    ax3 = fig.add_subplot(gs[1, :])
    for rto in df.index:
        ax3.plot(month_cols, df.loc[rto, month_cols], marker='o', linewidth=2, label=rto)
    ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax3.set_title('Seasonal Pattern of Percentage Changes')
    ax3.set_xlabel('Month')
    ax3.set_ylabel('Percent Change (%)')
    ax3.grid(linestyle='--', alpha=0.7)
    ax3.legend(title='RTO', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add an overall title
    plt.suptitle(f'Climate Change Impacts on Electricity Demand by RTO\n(Year: {year}, Polynomial Degree: {degree_of_fit})', fontsize=16, y=0.98)
    
    # Adjust the layout manually instead of using tight_layout
    plt.subplots_adjust(top=0.90, bottom=0.1, left=0.1, right=0.85)
    
    # Save the figure
    plt.savefig(os.path.join(output_dir, f'rto_demand_changes_combined_{year}_degree{degree_of_fit}.png'), dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    # Loop over years and polynomial degrees
    for year in [2023, 2024]:
        for degree_of_fit in [3, 4]:
            print(f"\nProcessing year {year} with polynomial degree {degree_of_fit}")
            main(year, degree_of_fit)