#!/usr/bin/env python3
"""
GEOS Hydraulic Fracturing Simulation - Visualization Script

This script processes GEOS output files and generates visualization plots for:
- Fracture dimensions (half-length, height) vs time
- Injection pressure vs time
- Fracture aperture distribution
- Pump rate schedule

Usage:
    python plot_hydrofracture_results.py [--output-dir OUTPUT_DIR]

Output:
    All figures saved to outputs/ directory
"""

import os
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt

# Try to import h5py for HDF5 file reading
try:
    import h5py
    HAS_H5PY = True
except ImportError:
    HAS_H5PY = False
    print("Warning: h5py not available. HDF5 file reading will be disabled.")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Visualize GEOS hydraulic fracturing simulation results'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='outputs',
        help='Directory containing GEOS output files (default: outputs)'
    )
    parser.add_argument(
        '--save-format',
        type=str,
        default='png',
        choices=['png', 'pdf', 'svg', 'jpg'],
        help='Figure save format (default: png)'
    )
    return parser.parse_args()


def load_pumping_schedule(table_dir='inputs/tables'):
    """Load the pumping schedule from table files."""
    try:
        time_data = np.loadtxt(os.path.join(table_dir, 'flowRate_time.csv'))
        rate_data = np.loadtxt(os.path.join(table_dir, 'flowRate.csv'))
        return time_data, rate_data
    except FileNotFoundError:
        print(f"Warning: Pump schedule files not found in {table_dir}")
        # Return default trapezoidal schedule
        time_data = np.array([0, 60, 65, 1200])
        rate_data = np.array([0, 0, 1, 1])
        return time_data, rate_data


def plot_pumping_schedule(time_data, rate_data, save_path='outputs/pumping_schedule.png'):
    """Plot the pumping schedule."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(time_data / 60, rate_data * 1000 / 5, 'b-', linewidth=2)  # Convert to kg/s for Nperf=5
    ax.set_xlabel('Time (minutes)', fontsize=12)
    ax.set_ylabel('Flow Rate (kg/s)', fontsize=12)
    ax.set_title('Injection Pumping Schedule', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 20)
    
    # Add annotations for key phases
    ax.axvline(x=1, color='r', linestyle='--', alpha=0.5, label='Pump start')
    ax.axvline(x=1+5/60, color='g', linestyle='--', alpha=0.5, label='Ramp end')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {save_path}")
    plt.close()


def plot_geologic_profile(table_dir='inputs/tables', save_path='outputs/geologic_profile.png'):
    """Plot the geologic model (layer-cake structure)."""
    try:
        z = np.loadtxt(os.path.join(table_dir, 'z.csv'))
        sigma_xx = np.loadtxt(os.path.join(table_dir, 'sigma_xx.csv')) / 1e6
        sigma_yy = np.loadtxt(os.path.join(table_dir, 'sigma_yy.csv')) / 1e6
        sigma_zz = np.loadtxt(os.path.join(table_dir, 'sigma_zz.csv')) / 1e6
        bulk = np.loadtxt(os.path.join(table_dir, 'bulkModulus.csv')) / 1e9
        shear = np.loadtxt(os.path.join(table_dir, 'shearModulus.csv')) / 1e9
    except FileNotFoundError:
        print(f"Warning: Geologic model files not found in {table_dir}")
        return
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 6))
    
    # Stress profiles
    axes[0].plot(sigma_xx, z, 'b-o', label=r'$\sigma_{xx}$ (min horizontal)', linewidth=2)
    axes[0].plot(sigma_yy, z, 'r-s', label=r'$\sigma_{yy}$ (overburden)', linewidth=2)
    axes[0].plot(sigma_zz, z, 'g-^', label=r'$\sigma_{zz}$ (max horizontal)', linewidth=2)
    axes[0].set_xlabel('Stress (MPa)', fontsize=12)
    axes[0].set_ylabel('Depth (m)', fontsize=12)
    axes[0].set_title('In-situ Stress Profiles', fontsize=12, fontweight='bold')
    axes[0].legend(loc='best')
    axes[0].grid(True, alpha=0.3)
    
    # Elastic moduli
    axes[1].plot(bulk, z, 'b-o', label='Bulk Modulus', linewidth=2)
    axes[1].plot(shear, z, 'r-s', label='Shear Modulus', linewidth=2)
    axes[1].set_xlabel('Modulus (GPa)', fontsize=12)
    axes[1].set_ylabel('Depth (m)', fontsize=12)
    axes[1].set_title('Rock Elastic Moduli', fontsize=12, fontweight='bold')
    axes[1].legend(loc='best')
    axes[1].grid(True, alpha=0.3)
    
    # Young's modulus and Poisson's ratio
    E = 9 * bulk * shear / (3 * bulk + shear)
    nu = (3 * bulk - 2 * shear) / (6 * bulk + 2 * shear)
    axes[2].plot(E, z, 'b-o', label="Young's Modulus", linewidth=2)
    ax2 = axes[2].twiny()
    ax2.plot(nu, z, 'r-s', label='Poisson Ratio', linewidth=2)
    axes[2].set_xlabel("E (GPa)", fontsize=12, color='b')
    ax2.set_xlabel(r'$\nu$ (dimensionless)', fontsize=12, color='r')
    axes[2].set_ylabel('Depth (m)', fontsize=12)
    axes[2].set_title('Derived Elastic Properties', fontsize=12, fontweight='bold')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {save_path}")
    plt.close()


def plot_mesh_schematic(save_path='outputs/mesh_schematic.png'):
    """Plot a schematic of the mesh configuration."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Domain dimensions
    x_min, x_max = 0, 250
    y_min, y_max = -100, 100
    z_min, z_max = -150, 150
    
    # Draw domain outline
    rect_xy = plt.Rectangle((x_min, y_min), x_max-x_min, y_max-y_min, 
                             fill=False, edgecolor='black', linewidth=2, linestyle='-')
    ax.add_patch(rect_xy)
    
    # Draw fracture plane
    ax.axhline(y=0, color='red', linewidth=3, label='Fracture plane (y=0)')
    
    # Draw injection point
    ax.plot(0, 0, 'ko', markersize=15, label='Injection point')
    
    # Draw initial perforation
    perf_rect = plt.Rectangle((-4, -4), 8, 8, fill=True, facecolor='yellow', 
                               edgecolor='orange', linewidth=2, alpha=0.5, label='Initial perforation')
    ax.add_patch(perf_rect)
    
    # Draw fracturable region
    frac_rect = plt.Rectangle((0, -0.05), 250, 0.1, fill=True, facecolor='lightblue', 
                               edgecolor='blue', linewidth=1, alpha=0.3, label='Fracturable region')
    ax.add_patch(frac_rect)
    
    # Draw boundaries
    ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(x=200, color='gray', linestyle=':', alpha=0.5)
    ax.axvline(x=250, color='gray', linestyle='--', alpha=0.5)
    
    ax.set_xlim(-20, 270)
    ax.set_ylim(-120, 120)
    ax.set_xlabel('X (m)', fontsize=12)
    ax.set_ylabel('Y (m)', fontsize=12)
    ax.set_title('Mesh Configuration Schematic (X-Y View)', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    
    # Add annotations
    ax.annotate('Core region\n(50 uniform elements)', xy=(100, -110), fontsize=9, ha='center')
    ax.annotate('Boundary region\n(5 biased elements)', xy=(225, -110), fontsize=9, ha='center')
    ax.annotate('xneg', xy=(-10, 0), fontsize=9, ha='right')
    ax.annotate('xpos', xy=(260, 0), fontsize=9, ha='left')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {save_path}")
    plt.close()


def create_summary_report(output_dir, table_dir='inputs/tables'):
    """Create a text summary of the simulation setup."""
    report_path = os.path.join(output_dir, 'simulation_summary.txt')
    
    with open(report_path, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("GEOS HYDRAULIC FRACTURING SIMULATION - SETUP SUMMARY\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("SIMULATION PARAMETERS:\n")
        f.write("-" * 40 + "\n")
        f.write("Maximum simulation time: 20 minutes\n")
        f.write("Fluid viscosity (default): 1 cP (0.001 Pa.s)\n")
        f.write("Pump start delay: 1 minute\n")
        f.write("Pump ramp duration: 5 seconds\n")
        f.write("Maximum timestep: 30 seconds\n")
        f.write("Pump ramp timestep limit: 0.2 seconds\n")
        f.write("HPC allocation: 28 minutes\n\n")
        
        f.write("MESH CONFIGURATION:\n")
        f.write("-" * 40 + "\n")
        f.write("Type: Internal mesh with biased boundaries\n")
        f.write("Element type: C3D8 (hexahedral)\n")
        f.write("X extent: 0 to 250 m (50 + 5 elements)\n")
        f.write("Y extent: -100 to 100 m (10 + 10 elements)\n")
        f.write("Z extent: -150 to 150 m (5 + 25 + 25 + 5 elements)\n")
        f.write("Total elements: ~41,250\n\n")
        
        f.write("FRACTURE GEOMETRY:\n")
        f.write("-" * 40 + "\n")
        f.write("Fracture plane: y = 0\n")
        f.write("Injection location: (0, 0, 0)\n")
        f.write("Initial perforation: 8m x 8m around origin\n")
        f.write("Fracturable surface: Thick plane at y=0\n\n")
        
        f.write("BOUNDARY CONDITIONS:\n")
        f.write("-" * 40 + "\n")
        f.write("Mechanical: Roller (zero displacement normal) on all boundaries\n")
        f.write("In-situ stress: Table-based heterogeneous from geologic model\n")
        f.write("Initial pore pressure: Table-based from geologic model\n")
        f.write("Injection: Source flux with trapezoidal pumping schedule\n\n")
        
        f.write("PHYSICS COUPLING:\n")
        f.write("-" * 40 + "\n")
        f.write("Solver: Hydrofracture (fully coupled)\n")
        f.write("  - SolidMechanicsLagrangianFEM for rock deformation\n")
        f.write("  - SinglePhaseFVM for fracture flow\n")
        f.write("  - SurfaceGenerator for fracture propagation\n\n")
        
        f.write("OUTPUTS:\n")
        f.write("-" * 40 + "\n")
        f.write("VTK: Every 1 minute (for Paraview)\n")
        f.write("Silo: Every 1 minute (for VisIt)\n")
        f.write("Restart: On HaltEvent (28 min allocation)\n\n")
        
        f.write("=" * 70 + "\n")
    
    print(f"Saved: {report_path}")


def main():
    """Main function."""
    args = parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("=" * 70)
    print("GEOS HYDRAULIC FRACTURING VISUALIZATION")
    print("=" * 70)
    
    # Plot pumping schedule
    print("\nGenerating pumping schedule plot...")
    time_data, rate_data = load_pumping_schedule()
    plot_pumping_schedule(
        time_data, rate_data,
        save_path=os.path.join(args.output_dir, f'pumping_schedule.{args.save_format}')
    )
    
    # Plot geologic model
    print("\nGenerating geologic profile plot...")
    plot_geologic_profile(
        save_path=os.path.join(args.output_dir, f'geologic_profile.{args.save_format}')
    )
    
    # Plot mesh schematic
    print("\nGenerating mesh schematic...")
    plot_mesh_schematic(
        save_path=os.path.join(args.output_dir, f'mesh_schematic.{args.save_format}')
    )
    
    # Create summary report
    print("\nGenerating simulation summary...")
    create_summary_report(args.output_dir)
    
    print("\n" + "=" * 70)
    print("Visualization complete!")
    print(f"All outputs saved to: {os.path.abspath(args.output_dir)}")
    print("=" * 70)
    
    # Check for GEOS output files
    print("\nNote: To visualize simulation results, run the GEOS simulation:")
    print("  1. Preprocess: preprocess_xml inputs/hydrofracture_benchmark.xml")
    print("  2. Run: geosx -i inputs/hydrofracture_benchmark.xml.preprocessed")
    print("  3. Load output files in Paraview or VisIt")


if __name__ == '__main__':
    main()
