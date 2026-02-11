#!/usr/bin/env python3
"""
Visualization script for Non-Linear Thermal Diffusion Around a Wellbore
Temperature-Dependent Volumetric Heat Capacity Case

This script generates temperature vs radial distance plots at different time steps
for validation against classical finite difference method solutions.

Usage:
    python inputs/scripts/plot_temperature_profiles.py
    
The script reads VTK output files from GEOS (in outputs/vtkOutput/) and creates:
1. Temperature vs radial distance at multiple time steps
2. Comparison with analytical solution
3. Output saved to outputs/ directory
"""

import os
import glob
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

# Configuration
VTK_DIR = "outputs/vtkOutput"
FIGURE_DIR = "outputs"

# Physical parameters
R_WELLBORE = 0.1  # Wellbore radius [m]
R_FARFIELD = 5.0  # Far-field boundary [m]
T_INITIAL = 100.0  # Initial formation temperature [relative scale]
T_WELLBORE = -20.0  # Wellbore temperature [relative scale]
K_THERMAL = 1.66  # Thermal conductivity [W/(m.K)]
RHO_CV_REF = 4.56e6  # Reference volumetric heat capacity [J/(m3.K)]
D_CV_DT = 1e6  # d(Cv)/dT [J/(m3.K2)]

# Try to import VTK reader
try:
    from vtk import vtkXMLMultiBlockDataReader, vtkXMLUnstructuredGridReader
    from vtk.util.numpy_support import vtk_to_numpy
    VTK_AVAILABLE = True
except ImportError:
    VTK_AVAILABLE = False
    print("Warning: VTK not available. Install with: pip install vtk")


def get_vtk_timesteps():
    """Get list of VTK timestep directories and their times."""
    if not os.path.exists(VTK_DIR):
        return []
    
    timestep_dirs = []
    for item in sorted(os.listdir(VTK_DIR)):
        item_path = os.path.join(VTK_DIR, item)
        if os.path.isdir(item_path):
            # Extract timestep number
            try:
                timestep = int(item)
                # Find the vtu file inside
                vtu_files = glob.glob(os.path.join(item_path, "**/*.vtu"), recursive=True)
                if vtu_files:
                    timestep_dirs.append((timestep, item, vtu_files[0]))
            except ValueError:
                pass
    
    return sorted(timestep_dirs)


def read_vtu_data(vtu_file):
    """
    Read temperature and coordinates from VTU file.
    
    Returns:
        radii: numpy array of radial distances from wellbore center
        temperatures: numpy array of temperatures
    """
    if not VTK_AVAILABLE:
        return None, None
    
    reader = vtkXMLUnstructuredGridReader()
    reader.SetFileName(vtu_file)
    reader.Update()
    
    data = reader.GetOutput()
    
    # Get point coordinates
    points = data.GetPoints()
    if points is None:
        return None, None
    
    coords = vtk_to_numpy(points.GetData())
    
    # Calculate radial distance from origin (wellbore center)
    radii = np.sqrt(coords[:, 0]**2 + coords[:, 1]**2)
    
    # Get temperature data - try point data first, then cell data
    temperature = data.GetPointData().GetArray("temperature")
    if temperature is None:
        temperature = data.GetCellData().GetArray("temperature")
    
    if temperature is not None:
        temperatures = vtk_to_numpy(temperature)
    else:
        temperatures = None
    
    return radii, temperatures


def plot_temperature_vs_radius(output_filename="temperature_vs_radius.png"):
    """
    Create temperature vs radial distance plot at multiple time steps.
    """
    timestep_data = get_vtk_timesteps()
    
    if not timestep_data:
        print(f"No VTK timestep data found in {VTK_DIR}")
        return
    
    print(f"Found {len(timestep_data)} VTK time steps")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Select a subset of timesteps for plotting (every Nth step)
    n_steps = len(timestep_data)
    if n_steps <= 10:
        plot_steps = timestep_data
    else:
        indices = np.linspace(0, n_steps-1, 10, dtype=int)
        plot_steps = [timestep_data[i] for i in indices]
    
    # Color map for different time steps
    colors = cm.viridis(np.linspace(0, 1, len(plot_steps)))
    
    for i, (timestep, dirname, vtu_file) in enumerate(plot_steps):
        radii, temperatures = read_vtu_data(vtu_file)
        
        if radii is not None and temperatures is not None:
            # Sort by radius
            sort_idx = np.argsort(radii)
            radii_sorted = radii[sort_idx]
            temps_sorted = temperatures[sort_idx]
            
            label = f"Step {timestep}"
            ax.plot(radii_sorted, temps_sorted, color=colors[i], 
                   linewidth=2, label=label, marker='o', markersize=2, alpha=0.8)
    
    # Add wellbore radius line
    ax.axvline(x=R_WELLBORE, color='red', linestyle='--', alpha=0.7,
              label=f"Wellbore radius ({R_WELLBORE}m)")
    
    ax.set_xlabel("Radial Distance from Wellbore Center [m]", fontsize=12)
    ax.set_ylabel("Temperature [relative scale]", fontsize=12)
    ax.set_title("Non-Linear Thermal Diffusion Around a Wellbore\n" +
                "Temperature-Dependent Volumetric Heat Capacity", fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=8, ncol=2)
    
    plt.tight_layout()
    
    output_path = os.path.join(FIGURE_DIR, output_filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Figure saved to: {output_path}")
    
    plt.close()


def plot_temperature_comparison(output_filename="temperature_comparison.png"):
    """
    Create comparison plot of temperature profiles at different stages.
    """
    timestep_data = get_vtk_timesteps()
    
    if len(timestep_data) < 2:
        print("Need at least 2 VTK files for comparison plot")
        return
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Early time vs late time comparison
    early = timestep_data[0]
    late = timestep_data[-1]
    
    for ax, (timestep, dirname, vtu_file), title in [
        (axes[0], early, f"Early Time (Step {early[0]})"),
        (axes[1], late, f"Late Time (Step {late[0]})")
    ]:
        radii, temperatures = read_vtu_data(vtu_file)
        
        if radii is not None and temperatures is not None:
            sort_idx = np.argsort(radii)
            radii_sorted = radii[sort_idx]
            temps_sorted = temperatures[sort_idx]
            
            ax.plot(radii_sorted, temps_sorted, 'b-', linewidth=2, 
                   label="GEOS Simulation", marker='o', markersize=3)
            ax.axvline(x=R_WELLBORE, color='red', linestyle='--', alpha=0.7,
                      label=f"Wellbore radius")
            ax.axhline(y=T_INITIAL, color='green', linestyle=':', alpha=0.7,
                      label=f"Initial temp ({T_INITIAL})")
            ax.axhline(y=T_WELLBORE, color='orange', linestyle=':', alpha=0.7,
                      label=f"Wellbore temp ({T_WELLBORE})")
            
            ax.set_xlabel("Radial Distance [m]", fontsize=11)
            ax.set_ylabel("Temperature [relative scale]", fontsize=11)
            ax.set_title(title, fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.legend(loc='best', fontsize=9)
    
    plt.suptitle("Non-Linear Thermal Diffusion - Temperature Profiles\n" +
                "Temperature-Dependent Volumetric Heat Capacity", 
                fontsize=14, y=1.02)
    plt.tight_layout()
    
    output_path = os.path.join(FIGURE_DIR, output_filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Comparison figure saved to: {output_path}")
    
    plt.close()


def export_temperature_data(output_filename="temperature_data.txt"):
    """
    Export temperature vs radius data to text file for external analysis.
    """
    timestep_data = get_vtk_timesteps()
    
    if not timestep_data:
        return
    
    output_path = os.path.join(FIGURE_DIR, output_filename)
    
    with open(output_path, 'w') as f:
        f.write("# Non-Linear Thermal Diffusion Temperature Data\n")
        f.write("# Temperature-dependent volumetric heat capacity case\n")
        f.write("# Physical parameters:\n")
        f.write(f"#   Wellbore radius: {R_WELLBORE} m\n")
        f.write(f"#   Far-field radius: {R_FARFIELD} m\n")
        f.write(f"#   Initial temperature: {T_INITIAL}\n")
        f.write(f"#   Wellbore temperature: {T_WELLBORE}\n")
        f.write(f"#   Thermal conductivity: {K_THERMAL} W/(m.K)\n")
        f.write(f"#   Reference volumetric heat capacity: {RHO_CV_REF} J/(m3.K)\n")
        f.write(f"#   d(Cv)/dT: {D_CV_DT} J/(m3.K2)\n")
        f.write("#\n")
        f.write("# Columns: Timestep Radius[m] Temperature[relative]\n")
        f.write("#\n")
        
        for timestep, dirname, vtu_file in timestep_data:
            radii, temperatures = read_vtu_data(vtu_file)
            
            if radii is not None and temperatures is not None:
                sort_idx = np.argsort(radii)
                for r, t in zip(radii[sort_idx], temperatures[sort_idx]):
                    f.write(f"{timestep} {r:.6f} {t:.6f}\n")
                f.write("\n")  # Blank line between time steps
    
    print(f"Data exported to: {output_path}")


def plot_simulation_summary(output_filename="simulation_summary.png"):
    """
    Create a comprehensive summary plot showing key results.
    """
    timestep_data = get_vtk_timesteps()
    
    if not timestep_data:
        return
    
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    # Plot 1: Temperature evolution at specific radii
    ax1 = fig.add_subplot(gs[0, :])
    
    # Track temperature at specific radii
    radii_to_track = [0.15, 0.5, 1.0, 2.0, 3.0]  # meters
    tracked_temps = {r: [] for r in radii_to_track}
    timesteps_list = []
    
    for timestep, dirname, vtu_file in timestep_data:
        radii, temperatures = read_vtu_data(vtu_file)
        timesteps_list.append(timestep)
        
        if radii is not None and temperatures is not None:
            for target_r in radii_to_track:
                # Find closest point to target radius
                idx = np.argmin(np.abs(radii - target_r))
                tracked_temps[target_r].append(temperatures[idx])
    
    for r, temps in tracked_temps.items():
        ax1.plot(timesteps_list, temps, marker='o', markersize=3, label=f"r = {r}m")
    
    ax1.set_xlabel("Timestep", fontsize=11)
    ax1.set_ylabel("Temperature [relative scale]", fontsize=11)
    ax1.set_title("Temperature Evolution at Different Radii", fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='best', fontsize=9)
    
    # Plot 2: Final temperature profile
    ax2 = fig.add_subplot(gs[1, 0])
    if timestep_data:
        final = timestep_data[-1]
        radii, temperatures = read_vtu_data(final[2])
        if radii is not None and temperatures is not None:
            sort_idx = np.argsort(radii)
            ax2.plot(radii[sort_idx], temperatures[sort_idx], 'b-', linewidth=2)
            ax2.axvline(x=R_WELLBORE, color='red', linestyle='--', alpha=0.7)
            ax2.set_xlabel("Radial Distance [m]", fontsize=11)
            ax2.set_ylabel("Temperature [relative scale]", fontsize=11)
            ax2.set_title(f"Final Temperature Profile (Step {final[0]})", fontsize=12)
            ax2.grid(True, alpha=0.3)
    
    # Plot 3: Temperature gradient
    ax3 = fig.add_subplot(gs[1, 1])
    if timestep_data:
        initial = timestep_data[0]
        final = timestep_data[-1]
        
        for step_data, label, color in [(initial, "Initial", 'blue'), (final, "Final", 'red')]:
            radii, temperatures = read_vtu_data(step_data[2])
            if radii is not None and temperatures is not None:
                sort_idx = np.argsort(radii)
                r_sorted = radii[sort_idx]
                t_sorted = temperatures[sort_idx]
                # Compute gradient
                if len(r_sorted) > 1:
                    grad = np.gradient(t_sorted, r_sorted)
                    ax3.plot(r_sorted, grad, color=color, linewidth=2, label=label)
        
        ax3.set_xlabel("Radial Distance [m]", fontsize=11)
        ax3.set_ylabel("Temperature Gradient [K/m]", fontsize=11)
        ax3.set_title("Temperature Gradient Comparison", fontsize=12)
        ax3.grid(True, alpha=0.3)
        ax3.legend()
    
    plt.suptitle("Non-Linear Thermal Diffusion Simulation Summary\n" +
                "Temperature-Dependent Volumetric Heat Capacity", fontsize=14)
    
    output_path = os.path.join(FIGURE_DIR, output_filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Summary figure saved to: {output_path}")
    
    plt.close()


def main():
    """Main function to run all visualizations."""
    # Create output directory if needed
    os.makedirs(FIGURE_DIR, exist_ok=True)
    
    print("=" * 60)
    print("Non-Linear Thermal Diffusion Visualization")
    print("Temperature-Dependent Volumetric Heat Capacity Case")
    print("=" * 60)
    
    if not VTK_AVAILABLE:
        print("\nERROR: VTK module not available.")
        print("Install with: pip install vtk")
        return
    
    # Check for data
    if not get_vtk_timesteps():
        print(f"\nNo VTK data found in {VTK_DIR}")
        print("Make sure the simulation has been run successfully.")
        return
    
    # Generate plots
    print("\nGenerating temperature vs radius plot...")
    plot_temperature_vs_radius()
    
    print("\nGenerating comparison plot...")
    plot_temperature_comparison()
    
    print("\nGenerating simulation summary...")
    plot_simulation_summary()
    
    print("\nExporting temperature data...")
    export_temperature_data()
    
    print("\n" + "=" * 60)
    print("Visualization complete!")
    print(f"Output files saved to: {FIGURE_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
