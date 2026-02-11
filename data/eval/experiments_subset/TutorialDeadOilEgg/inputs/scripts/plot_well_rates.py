#!/usr/bin/env python3
"""
================================================================================
Egg Model Well Production Rate Visualization Script
================================================================================

This script reads HDF5 time history files from GEOS simulation output and
generates plots of well production/injection rates over time.

Usage:
    python plot_well_rates.py

Output:
    outputs/well_rates_plot.png - Combined plot of all well rates
    outputs/well_rates_data.csv - CSV export of rate data
================================================================================
"""

import h5py
import numpy as np
import matplotlib.pyplot as plt
import os
import csv
from pathlib import Path

# Configuration
OUTPUT_DIR = Path("outputs")
INPUT_DIR = Path("inputs")

# Well file names (HDF5 format)
WELL_FILES = {
    "Producer 1": OUTPUT_DIR / "wellRateHistory1.hdf5",
    "Producer 2": OUTPUT_DIR / "wellRateHistory2.hdf5",
    "Producer 3": OUTPUT_DIR / "wellRateHistory3.hdf5",
    "Producer 4": OUTPUT_DIR / "wellRateHistory4.hdf5",
}

# Color scheme for wells
COLORS = {
    "Producer 1": "#1f77b4",  # Blue
    "Producer 2": "#ff7f0e",  # Orange
    "Producer 3": "#2ca02c",  # Green
    "Producer 4": "#d62728",  # Red
}


def read_hdf5_time_history(filepath):
    """
    Read time history data from GEOS HDF5 output file.
    
    Parameters:
        filepath: Path to HDF5 file
        
    Returns:
        tuple: (time_array, data_array) or (None, None) if file not found
    """
    if not filepath.exists():
        print(f"Warning: File not found: {filepath}")
        return None, None
    
    try:
        with h5py.File(filepath, 'r') as f:
            # GEOS HDF5 structure:
            # - 'time' dataset contains time values
            # - 'value' dataset contains the field values
            if 'time' in f and 'value' in f:
                time = np.array(f['time'])
                value = np.array(f['value'])
                return time, value
            else:
                print(f"Warning: HDF5 file missing 'time' or 'value' datasets: {filepath}")
                # Try alternative structure
                for key in f.keys():
                    print(f"  Available key: {key}")
                return None, None
    except Exception as e:
        print(f"Error reading HDF5 file {filepath}: {e}")
        return None, None


def convert_time_units(time_seconds, unit='days'):
    """Convert time from seconds to specified unit."""
    if unit == 'seconds':
        return time_seconds
    elif unit == 'minutes':
        return time_seconds / 60.0
    elif unit == 'hours':
        return time_seconds / 3600.0
    elif unit == 'days':
        return time_seconds / 86400.0
    elif unit == 'years':
        return time_seconds / (86400.0 * 365.25)
    else:
        return time_seconds


def convert_rate_units(rate_kg_s, unit='kg/day'):
    """Convert rate from kg/s to specified unit."""
    if unit == 'kg/s':
        return rate_kg_s
    elif unit == 'kg/day':
        return rate_kg_s * 86400.0
    elif unit == 'kg/year':
        return rate_kg_s * 86400.0 * 365.25
    else:
        return rate_kg_s


def plot_well_rates(time_unit='days', rate_unit='kg/day'):
    """
    Create publication-quality plot of well rates.
    
    Parameters:
        time_unit: Time unit for x-axis ('seconds', 'minutes', 'hours', 'days', 'years')
        rate_unit: Rate unit for y-axis ('kg/s', 'kg/day', 'kg/year')
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Egg Model - Well Production Rates', fontsize=14, fontweight='bold')
    
    all_data = {}
    
    # Read data for each well
    for well_name, filepath in WELL_FILES.items():
        time, rate = read_hdf5_time_history(filepath)
        if time is not None and rate is not None:
            # Convert units
            time_conv = convert_time_units(time, time_unit)
            rate_conv = convert_rate_units(rate, rate_unit)
            all_data[well_name] = (time_conv, rate_conv)
    
    if not all_data:
        print("No well rate data found. Please run the simulation first.")
        plt.close(fig)
        return
    
    # Plot individual well rates
    well_names = list(WELL_FILES.keys())
    for idx, (ax, well_name) in enumerate(zip(axes.flat, well_names)):
        if well_name in all_data:
            time, rate = all_data[well_name]
            ax.plot(time, rate, color=COLORS[well_name], linewidth=1.5, label=well_name)
            ax.set_xlabel(f'Time [{time_unit}]', fontsize=10)
            ax.set_ylabel(f'Rate [{rate_unit}]', fontsize=10)
            ax.set_title(well_name, fontsize=11, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='best')
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / 'well_rates_plot.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved well rates plot to: {output_path}")
    plt.close(fig)
    
    # Create combined plot
    fig, ax = plt.subplots(figsize=(12, 6))
    for well_name, (time, rate) in all_data.items():
        ax.plot(time, rate, color=COLORS[well_name], linewidth=1.5, label=well_name)
    
    ax.set_xlabel(f'Time [{time_unit}]', fontsize=12)
    ax.set_ylabel(f'Production Rate [{rate_unit}]', fontsize=12)
    ax.set_title('Egg Model - All Producer Well Rates', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=10)
    
    combined_path = OUTPUT_DIR / 'well_rates_combined.png'
    plt.savefig(combined_path, dpi=300, bbox_inches='tight')
    print(f"Saved combined well rates plot to: {combined_path}")
    plt.close(fig)
    
    return all_data


def export_to_csv(all_data, time_unit='days', rate_unit='kg/day'):
    """
    Export well rate data to CSV format.
    
    Parameters:
        all_data: Dictionary of well data
        time_unit: Time unit for output
        rate_unit: Rate unit for output
    """
    if not all_data:
        return
    
    # Find common time points (use first well as reference)
    first_well = list(all_data.keys())[0]
    time_ref = all_data[first_well][0]
    
    csv_path = OUTPUT_DIR / 'well_rates_data.csv'
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        header = [f'Time_{time_unit}'] + [f'{well}_{rate_unit}' for well in all_data.keys()]
        writer.writerow(header)
        
        # Data rows
        for i in range(len(time_ref)):
            row = [time_ref[i]]
            for well_name in all_data.keys():
                time, rate = all_data[well_name]
                if i < len(rate):
                    row.append(rate[i])
                else:
                    row.append('')
            writer.writerow(row)
    
    print(f"Exported well rate data to: {csv_path}")


def print_statistics(all_data):
    """Print summary statistics for each well."""
    if not all_data:
        return
    
    print("\n" + "="*70)
    print("WELL PRODUCTION STATISTICS")
    print("="*70)
    
    for well_name, (time, rate) in all_data.items():
        print(f"\n{well_name}:")
        print(f"  Simulation duration: {time[-1]:.2f} days")
        print(f"  Initial rate: {rate[0]:.2e} kg/day")
        print(f"  Final rate: {rate[-1]:.2e} kg/day")
        print(f"  Maximum rate: {rate.max():.2e} kg/day")
        print(f"  Minimum rate: {rate.min():.2e} kg/day")
        print(f"  Average rate: {rate.mean():.2e} kg/day")
        print(f"  Cumulative production: {np.trapz(rate, time):.2e} kg")


def main():
    """Main execution function."""
    print("="*70)
    print("EGG MODEL WELL RATE VISUALIZATION")
    print("="*70)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Plot well rates
    print("\nGenerating well rate plots...")
    all_data = plot_well_rates(time_unit='days', rate_unit='kg/day')
    
    # Export to CSV
    if all_data:
        print("\nExporting data to CSV...")
        export_to_csv(all_data)
        
        # Print statistics
        print_statistics(all_data)
    
    print("\n" + "="*70)
    print("Visualization complete!")
    print("="*70)


if __name__ == "__main__":
    main()
