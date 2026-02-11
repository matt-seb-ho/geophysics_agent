#!/usr/bin/env python3
"""
Post-processing script for Extended Drucker-Prager Wellbore Simulation

This script reads GEOS output files and generates publication-quality plots for:
1. Wellbore pressure evolution vs time
2. Wellbore radial contraction/displacement vs time
3. Stress path on the wellbore surface (p-q diagram)
4. Radial stress distribution (analytical reference)

Usage:
    python plot_edp_wellbore_results.py

Output:
    - wellbore_pressure_evolution.png
    - wellbore_contraction.png
    - stress_path_wellbore.png
    - radial_stress_distribution.png
    - simulation_summary.txt

Reference: Chen and Abousleiman (2017)
"""

import h5py
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for batch processing
import matplotlib.pyplot as plt
import os

# Output directory (relative to workspace)
OUTPUT_DIR = '../../outputs'


def read_time_history(filename):
    """
    Read GEOS TimeHistory HDF5 file with correct structure.
    
    Parameters:
        filename: Name of the HDF5 file in OUTPUT_DIR
        
    Returns:
        time: Array of time values
        data: Array of field data (time_steps x elements x components)
    """
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found")
        return None, None
    
    with h5py.File(filepath, 'r') as f:
        # Find the data group (not the Time dataset)
        for key in f.keys():
            if 'Time' not in key and key != 'time':
                data = np.array(f[key][:])
                # Find the corresponding Time dataset
                time_key = key + ' Time'
                if time_key in f:
                    time = np.array(f[time_key][:])
                else:
                    time = None
                return time, data
    
    return None, None


def plot_wellbore_pressure_evolution():
    """Plot the applied wellbore pressure evolution over time."""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Loading history from table function
    time = np.array([0.0, 1.0])
    pressure = np.array([-11.25, -2.0])  # MPa
    
    ax.plot(time, -pressure, 'b-', linewidth=2, label='Applied wellbore pressure')
    ax.axhline(y=11.25, color='r', linestyle='--', alpha=0.5, label=r'$\sigma_h$ (initial)')
    ax.axhline(y=2.0, color='g', linestyle='--', alpha=0.5, label=r'$P_{w,f}$ (final)')
    
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Wellbore Pressure [MPa]')
    ax.set_title('Wellbore Pressure Evolution')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    ax.set_xlim(0, 1.02)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'wellbore_pressure_evolution.png'), dpi=300)
    print(f"  Saved: wellbore_pressure_evolution.png")
    plt.close()


def plot_wellbore_contraction():
    """Plot the wellbore radial contraction from displacement history."""
    time, displacement_data = read_time_history('displacementHistory.hdf5')
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    if displacement_data is not None and time is not None:
        # Average displacement magnitude over all nodes at each time step
        if len(displacement_data.shape) == 3:
            # Shape: (time_steps, nodes, components)
            disp_magnitude = np.sqrt(np.sum(displacement_data**2, axis=2))
            mean_disp = np.mean(disp_magnitude, axis=1)
            max_disp = np.max(disp_magnitude, axis=1)
            
            ax.plot(time, mean_disp * 1000, 'b-', linewidth=2, label='Mean displacement')
            ax.plot(time, max_disp * 1000, 'r--', linewidth=1.5, label='Max displacement')
            ax.set_ylabel('Displacement magnitude [mm]')
        else:
            ax.plot(time, displacement_data, 'b-', linewidth=2)
            ax.set_ylabel('Displacement [m]')
        
        ax.set_xlabel('Time [s]')
        ax.set_title('Wellbore Radial Contraction')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        ax.set_xlim(0, 1.02)
    else:
        ax.text(0.5, 0.5, 'Displacement data not available', 
                ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_xlabel('Time [s]')
        ax.set_ylabel('Displacement [m]')
        ax.set_title('Wellbore Radial Contraction')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'wellbore_contraction.png'), dpi=300)
    print(f"  Saved: wellbore_contraction.png")
    plt.close()


def plot_stress_path_wellbore():
    """
    Plot the stress path (p-q diagram) at the wellbore wall.
    
    p = mean stress = (S_xx + S_yy + S_zz) / 3
    q = deviatoric stress = sqrt(3 * J2)
    """
    time, stress_data = read_time_history('stressHistory_rock.hdf5')
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    if stress_data is not None and time is not None and len(stress_data.shape) == 3:
        # Calculate mean and deviatoric stress at the wellbore wall
        # Use first few elements as proxy for wellbore wall
        n_wall_elements = min(100, stress_data.shape[1])
        wall_stress = stress_data[:, :n_wall_elements, :]
        
        # Average over wall elements
        mean_stress = np.mean(wall_stress, axis=1)
        
        S_xx = mean_stress[:, 0]
        S_yy = mean_stress[:, 1]
        S_zz = mean_stress[:, 2]
        
        # Mean stress p
        p = (S_xx + S_yy + S_zz) / 3.0
        
        # Deviatoric stress q (von Mises equivalent)
        S_mean = p
        S_dev_xx = S_xx - S_mean
        S_dev_yy = S_yy - S_mean
        S_dev_zz = S_zz - S_mean
        
        J2 = 0.5 * (S_dev_xx**2 + S_dev_yy**2 + S_dev_zz**2) + \
             mean_stress[:, 3]**2 + mean_stress[:, 4]**2 + mean_stress[:, 5]**2
        q = np.sqrt(3.0 * J2)
        
        # Plot stress path
        scatter = ax.scatter(-p / 1e6, q / 1e6, c=time, cmap='viridis', 
                           s=50, edgecolors='black', linewidths=0.5)
        ax.plot(-p / 1e6, q / 1e6, 'k-', linewidth=0.5, alpha=0.5)
        
        # Add colorbar for time
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Time [s]')
        
        # Add reference yield surface (simplified Extended Drucker-Prager)
        p_yield = np.linspace(0, 15, 100)
        phi_initial = 15.27 * np.pi / 180
        q_yield = np.sqrt(3) * p_yield * np.sin(phi_initial) / (np.sqrt(3) - np.sin(phi_initial))
        ax.plot(p_yield, q_yield, 'r--', linewidth=2, label='Initial yield surface')
        
        ax.set_xlabel('Mean stress $p$ [MPa]')
        ax.set_ylabel('Deviatoric stress $q$ [MPa]')
        ax.set_title('Stress Path at Wellbore Wall')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
    else:
        ax.text(0.5, 0.5, 'Stress data not available', 
                ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_xlabel('Mean stress $p$ [MPa]')
        ax.set_ylabel('Deviatoric stress $q$ [MPa]')
        ax.set_title('Stress Path at Wellbore Wall')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'stress_path_wellbore.png'), dpi=300)
    print(f"  Saved: stress_path_wellbore.png")
    plt.close()


def plot_radial_stress_distribution():
    """
    Plot the radial distribution of principal stresses.
    Includes analytical elastic solution for reference.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    r_w = 0.1  # Wellbore radius
    r_max = 10.0  # Far-field radius
    
    r = np.linspace(r_w, r_max, 200)
    
    # Analytical elastic solution for isotropic loading
    sigma_h = 11.25e6  # Horizontal stress magnitude
    P_w = 2.0e6  # Final wellbore pressure
    
    # Elastic solution: sigma_rr and sigma_tt
    sigma_rr = -sigma_h - (sigma_h - P_w) * (r_w / r)**2
    sigma_tt = -sigma_h + (sigma_h - P_w) * (r_w / r)**2
    sigma_zz = np.full_like(r, -15.0e6)  # Vertical stress (constant)
    
    ax.plot(r / r_w, -sigma_rr / 1e6, 'b-', linewidth=2, label=r'$\sigma_{rr}$')
    ax.plot(r / r_w, -sigma_tt / 1e6, 'r-', linewidth=2, label=r'$\sigma_{\theta\theta}$')
    ax.plot(r / r_w, -sigma_zz / 1e6, 'g-', linewidth=2, label=r'$\sigma_{zz}$')
    
    ax.axvline(x=1.0, color='k', linestyle='--', alpha=0.3)
    ax.text(1.1, 5, 'Wellbore wall', rotation=90, va='bottom', fontsize=10)
    
    ax.set_xlabel('Normalized radial distance $r/r_w$')
    ax.set_ylabel('Stress [MPa]')
    ax.set_title('Radial Stress Distribution (Analytical Elastic Solution)')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best')
    ax.set_xlim(0.5, 100)
    ax.set_xscale('log')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'radial_stress_distribution.png'), dpi=300)
    print(f"  Saved: radial_stress_distribution.png")
    plt.close()


def generate_summary():
    """Generate a text summary of the simulation results."""
    summary_file = os.path.join(OUTPUT_DIR, 'simulation_summary.txt')
    
    with open(summary_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("Extended Drucker-Prager Wellbore Simulation Summary\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("Simulation Parameters:\n")
        f.write("-" * 40 + "\n")
        f.write("Model: Extended Drucker-Prager with strain hardening\n")
        f.write("Bulk modulus K: 500 MPa\n")
        f.write("Shear modulus G: 300 MPa\n")
        f.write("Initial friction angle: 15.27 degrees\n")
        f.write("Residual friction angle: 23.05 degrees\n")
        f.write("Hardening rate: 0.01\n")
        f.write("Dilation ratio: 1.0 (associated flow)\n")
        f.write("Cohesion: 0.0 MPa\n\n")
        
        f.write("In-situ Stress Conditions:\n")
        f.write("-" * 40 + "\n")
        f.write("Horizontal stress: -11.25 MPa (isotropic)\n")
        f.write("Vertical stress: -15.0 MPa\n\n")
        
        f.write("Loading History:\n")
        f.write("-" * 40 + "\n")
        f.write("Initial wellbore pressure: 11.25 MPa\n")
        f.write("Final wellbore pressure: 2.0 MPa\n")
        f.write("Total simulation time: 1.02 s\n\n")
        
        f.write("Expected Results:\n")
        f.write("-" * 40 + "\n")
        f.write("- Wellbore contraction due to pressure reduction\n")
        f.write("- Plastic zone development around wellbore\n")
        f.write("- Stress redistribution from elastic to plastic solution\n")
        f.write("- Strain hardening behavior after yield initiation\n\n")
        
        f.write("Reference:\n")
        f.write("-" * 40 + "\n")
        f.write("Chen and Abousleiman (2017)\n")
        f.write("\"Exact drained solution for wellbore problems\n")
        f.write(" with the Extended Drucker-Prager model\"\n\n")
        
        f.write("Output Files:\n")
        f.write("-" * 40 + "\n")
        
        # List generated files
        if os.path.exists(OUTPUT_DIR):
            files = sorted(os.listdir(OUTPUT_DIR))
            for fname in files:
                f.write(f"  - {fname}\n")
        
        f.write("\n" + "=" * 70 + "\n")
    
    print(f"  Saved: simulation_summary.txt")


def main():
    """Main function to generate all plots."""
    print("=" * 70)
    print("Extended Drucker-Prager Wellbore - Post-processing")
    print("=" * 70)
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Set up matplotlib style
    plt.rcParams['font.size'] = 12
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['figure.dpi'] = 150
    
    # Generate plots
    print("\nGenerating plots...")
    plot_wellbore_pressure_evolution()
    plot_wellbore_contraction()
    plot_stress_path_wellbore()
    plot_radial_stress_distribution()
    
    # Generate summary
    print("\nGenerating summary...")
    generate_summary()
    
    print("\n" + "=" * 70)
    print("Post-processing complete!")
    print(f"Results saved to: {OUTPUT_DIR}/")
    print("=" * 70)


if __name__ == '__main__':
    main()
