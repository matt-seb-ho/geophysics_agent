#!/usr/bin/env python3
"""
================================================================================
Visualization Script for Non-Linear Thermal Diffusion Simulation
================================================================================

This script generates publication-quality plots for the non-linear thermal 
diffusion problem around a wellbore with temperature-dependent volumetric 
heat capacity.

The script creates:
1. Temperature vs radial distance at multiple times (analytical reference)
2. Temperature evolution at specific radial locations
3. Illustration of non-linear heat capacity effects

Usage:
    python plot_thermal_results.py

Output files are saved to outputs/ directory.
================================================================================
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from pathlib import Path

# Configure matplotlib style
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['legend.fontsize'] = 9

# Paths
OUTPUT_DIR = Path(__file__).parent.parent.parent / "outputs"


def erf_approx(x):
    """Approximation of the error function using a polynomial fit."""
    # Abramowitz and Stegun approximation
    a1 =  0.254829592
    a2 = -0.284496736
    a3 =  1.421413741
    a4 = -1.453152027
    a5 =  1.061405429
    p  =  0.3275911
    
    sign = np.sign(x)
    x = np.abs(x)
    
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * np.exp(-x * x)
    
    return sign * y


def plot_temperature_profiles(save_dir):
    """
    Generate temperature vs radial distance plots at different times.
    
    Uses the analytical solution for linear thermal diffusion as a reference
    to compare with the GEOS non-linear simulation results.
    """
    # Problem parameters (matching the simulation)
    r_well = 0.1      # Wellbore radius [m]
    r_far = 5.0       # Far-field radius [m]
    T_wellbore_abs = -20.0  # Wellbore temperature [°C] (reference 0 + scale -20)
    T_farfield_abs = 100.0  # Far-field temperature [°C]
    
    # Radial positions for plotting
    r = np.linspace(r_well, r_far, 200)
    
    # Thermal diffusivity (approximate for this problem)
    k_thermal = 1.5       # Thermal conductivity [W/(m·K)]
    rho_Cv = 2.0e6        # Volumetric heat capacity [J/(m³·K)]
    alpha = k_thermal / rho_Cv  # Thermal diffusivity [m²/s]
    
    # Time points for plotting (seconds) - matching simulation output times
    times = [0, 10000, 20000, 50000, 100000]
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    colors = cm.viridis(np.linspace(0, 1, len(times)))
    
    for i, t in enumerate(times):
        if t == 0:
            # Initial condition
            T_profile = np.full_like(r, T_farfield_abs)
            ax.plot(r, T_profile, '-', color=colors[i], 
                    label=f't = 0 s (initial)', linewidth=2)
        else:
            # Linear diffusion solution (error function)
            eta = (r - r_well) / (2 * np.sqrt(alpha * t))
            T_profile = T_wellbore_abs + (T_farfield_abs - T_wellbore_abs) * erf_approx(eta)
            
            ax.plot(r, T_profile, '-', color=colors[i], 
                    label=f't = {t/1000:.0f} ks ({t/3600:.1f} hr)', linewidth=2)
    
    # Mark boundaries
    ax.axvline(x=r_well, color='red', linestyle='--', alpha=0.5, linewidth=1)
    ax.axvline(x=r_far, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    # Add boundary labels
    ax.text(r_well + 0.05, 50, 'Wellbore\nwall', fontsize=8, color='red')
    ax.text(r_far - 0.8, 50, 'Far-field\nboundary', fontsize=8, color='gray')
    
    ax.set_xlabel('Radial Distance, r [m]')
    ax.set_ylabel('Temperature, T [°C]')
    ax.set_title('Temperature Profiles Around Wellbore\n(Linear Diffusion Reference Solution)')
    ax.legend(loc='right', framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, r_far])
    ax.set_ylim([-30, 120])
    
    plt.tight_layout()
    save_path = save_dir / 'temperature_radial_profiles.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {save_path}")
    plt.close()


def plot_temperature_evolution(save_dir):
    """Plot temperature evolution at specific radial locations."""
    # Problem parameters
    r_well = 0.1
    T_wellbore_abs = -20.0
    T_farfield_abs = 100.0
    
    # Thermal diffusivity
    k_thermal = 1.5
    rho_Cv = 2.0e6
    alpha = k_thermal / rho_Cv
    
    # Radial positions of interest (meters from center)
    r_positions = [0.1, 0.3, 0.5, 1.0, 2.0, 3.0]
    
    # Time array (logarithmic)
    t = np.logspace(2, 5.2, 200)  # 100s to ~160,000s
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    colors = cm.plasma(np.linspace(0, 1, len(r_positions)))
    
    for i, r in enumerate(r_positions):
        # Temperature evolution (error function solution)
        eta = (r - r_well) / (2 * np.sqrt(alpha * t))
        T = T_wellbore_abs + (T_farfield_abs - T_wellbore_abs) * erf_approx(eta)
        
        ax.semilogx(t, T, '-', color=colors[i], 
                   label=f'r = {r} m', linewidth=2)
    
    # Reference lines
    ax.axhline(y=T_wellbore_abs, color='blue', linestyle='--', alpha=0.5, label='Wellbore temp')
    ax.axhline(y=T_farfield_abs, color='red', linestyle='--', alpha=0.5, label='Far-field temp')
    
    ax.set_xlabel('Time, t [s]')
    ax.set_ylabel('Temperature, T [°C]')
    ax.set_title('Temperature Evolution at Different Radial Locations\n(Linear Diffusion Reference)')
    ax.legend(loc='right', framealpha=0.9)
    ax.grid(True, alpha=0.3, which='both')
    ax.set_xlim([100, 200000])
    ax.set_ylim([-30, 120])
    
    plt.tight_layout()
    save_path = save_dir / 'temperature_time_evolution.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {save_path}")
    plt.close()


def plot_nonlinear_effect(save_dir):
    """
    Illustrate the effect of temperature-dependent volumetric heat capacity.
    
    Shows how the non-linear heat capacity affects the temperature profile
    compared to the constant heat capacity (linear) case.
    """
    # Problem parameters
    r_well = 0.1
    r_far = 5.0
    T_wellbore_abs = -20.0
    T_farfield_abs = 100.0
    t = 50000  # seconds
    
    r = np.linspace(r_well, r_far, 200)
    
    k_thermal = 1.5
    
    # Linear case (constant heat capacity)
    Cv_ref = 2.0e6  # J/(m3*K)
    alpha_linear = k_thermal / Cv_ref
    
    eta_linear = (r - r_well) / (2 * np.sqrt(alpha_linear * t))
    T_linear = T_wellbore_abs + (T_farfield_abs - T_wellbore_abs) * erf_approx(eta_linear)
    
    # Non-linear case (temperature-dependent heat capacity)
    # Cv(T) = Cv_ref + dCv_dT * (T - T_ref)
    # dCv_dT > 0 means higher heat capacity at higher temperatures
    # This means slower diffusion where it's hot, faster where it's cold
    dCv_dT = 1.0e6  # J/(m3*K2)
    
    # Effective diffusivity varies with position
    Cv_effective = Cv_ref + dCv_dT * (T_linear - 0)  # reference temp = 0
    alpha_effective = k_thermal / Cv_effective
    
    # Modified solution (approximate)
    eta_nonlinear = (r - r_well) / (2 * np.sqrt(alpha_effective * t))
    T_nonlinear = T_wellbore_abs + (T_farfield_abs - T_wellbore_abs) * erf_approx(eta_nonlinear)
    
    # Create figure with subplots
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    
    # Plot 1: Temperature profiles comparison
    ax1.plot(r, T_linear, 'b-', linewidth=2.5, label='Linear (constant Cv)')
    ax1.plot(r, T_nonlinear, 'r--', linewidth=2.5, label='Non-linear (Cv(T))')
    ax1.axvline(x=r_well, color='gray', linestyle=':', alpha=0.5)
    ax1.axvline(x=r_far, color='gray', linestyle=':', alpha=0.5)
    
    ax1.set_xlabel('Radial Distance, r [m]')
    ax1.set_ylabel('Temperature, T [°C]')
    ax1.set_title(f'Temperature Profiles at t = {t/1000:.0f} ks')
    ax1.legend(framealpha=0.9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([0, r_far])
    ax1.set_ylim([-30, 120])
    
    # Plot 2: Volumetric heat capacity variation
    Cv_linear = np.full_like(r, Cv_ref / 1e6)
    Cv_nonlinear_plot = (Cv_ref + dCv_dT * (T_nonlinear - 0)) / 1e6
    
    ax2.plot(r, Cv_linear, 'b-', linewidth=2.5, label='Linear (constant)')
    ax2.plot(r, Cv_nonlinear_plot, 'r--', linewidth=2.5, label='Non-linear (Cv(T))')
    ax2.axvline(x=r_well, color='gray', linestyle=':', alpha=0.5)
    ax2.axvline(x=r_far, color='gray', linestyle=':', alpha=0.5)
    
    ax2.set_xlabel('Radial Distance, r [m]')
    ax2.set_ylabel('Volumetric Heat Capacity, Cv [MJ/(m³·K)]')
    ax2.set_title('Temperature-Dependent Volumetric Heat Capacity')
    ax2.legend(framealpha=0.9)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([0, r_far])
    
    # Plot 3: Thermal diffusivity variation
    alpha_linear_plot = np.full_like(r, alpha_linear * 1e6)  # Scale for visualization
    alpha_nonlinear_plot = alpha_effective * 1e6
    
    ax3.plot(r, alpha_linear_plot, 'b-', linewidth=2.5, label='Linear (constant)')
    ax3.plot(r, alpha_nonlinear_plot, 'r--', linewidth=2.5, label='Non-linear')
    ax3.axvline(x=r_well, color='gray', linestyle=':', alpha=0.5)
    ax3.axvline(x=r_far, color='gray', linestyle=':', alpha=0.5)
    
    ax3.set_xlabel('Radial Distance, r [m]')
    ax3.set_ylabel(r'Thermal Diffusivity, α [×10⁻⁶ m²/s]')
    ax3.set_title('Effective Thermal Diffusivity')
    ax3.legend(framealpha=0.9)
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim([0, r_far])
    
    plt.tight_layout()
    save_path = save_dir / 'nonlinear_effect_comparison.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {save_path}")
    plt.close()
    
    # Print key parameters
    print("\n" + "="*60)
    print("Non-Linear Thermal Diffusion - Key Parameters")
    print("="*60)
    print(f"Reference volumetric heat capacity: {Cv_ref/1e6:.2f} MJ/(m³·K)")
    print(f"dCv/dT: {dCv_dT/1e3:.1f} kJ/(m³·K²)")
    print(f"Thermal conductivity: {k_thermal:.1f} W/(m·K)")
    print(f"Thermal diffusivity (linear): {alpha_linear*1e6:.2f} × 10⁻⁶ m²/s")
    print(f"Wellbore temperature: {T_wellbore_abs:.1f}°C")
    print(f"Far-field temperature: {T_farfield_abs:.1f}°C")
    print("="*60)


def main():
    """Main function to generate all plots."""
    print("=" * 60)
    print("Non-Linear Thermal Diffusion Visualization")
    print("=" * 60)
    
    # Create output directory if needed
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate plots
    print("\nGenerating reference plots...")
    plot_temperature_profiles(OUTPUT_DIR)
    plot_temperature_evolution(OUTPUT_DIR)
    plot_nonlinear_effect(OUTPUT_DIR)
    
    print("\n" + "=" * 60)
    print("Visualization complete!")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)
    
    # List generated files
    plots = list(OUTPUT_DIR.glob("*.png"))
    if plots:
        print("\nGenerated plots:")
        for p in sorted(plots):
            print(f"  - {p.name}")


if __name__ == "__main__":
    main()
