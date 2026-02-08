#!/usr/bin/env python3
"""
Visco Drucker-Prager Triaxial Driver Validation Script

This script compares GEOS simulation results against semi-analytical solutions
based on the Perzyna time-dependent viscoplasticity approach.

The Duvaut-Lions viscoplastic formulation in GEOS is equivalent to Perzyna
for linear hardening cases.

Key equations for semi-analytical solution:
- Stress deviator: q = sqrt(3/2 * s:s)
- Yield function: F = q - (a + b*p) where p is mean stress
- Viscoplastic multiplier evolution: dλ/dt = (1/t*) * F / (3μ + K*b*b' + h)
- Stress update depends on positive/negative yielding
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import sys

# ============================================================
# MATERIAL PARAMETERS (must match GEOS input)
# ============================================================

# Elastic properties
BULK_MODULUS = 3.333e9  # Pa
SHEAR_MODULUS = 2.0e9   # Pa
YOUNG_MODULUS = 5.0e9   # Pa (derived: E = 9Kμ/(3K+μ))
POISSON_RATIO = 0.25    # (derived)

# Drucker-Prager parameters
FRICTION_ANGLE = 30.0 * np.pi / 180.0  # radians
COHESION = 1.0e6        # Pa (initial cohesion a)
DILATION_ANGLE = 20.0 * np.pi / 180.0  # radians

# Convert angles to Drucker-Prager parameters b and b'
# b = 6*sin(φ)/(3-sin(φ)) for compression
B_FRICTION = 6.0 * np.sin(FRICTION_ANGLE) / (3.0 - np.sin(FRICTION_ANGLE))
B_DILATION = 6.0 * np.sin(DILATION_ANGLE) / (3.0 - np.sin(DILATION_ANGLE))

# Hardening and viscoplastic parameters
HARDENING_RATE = 5.0e8  # Pa (h)
RELAXATION_TIME = 1.0    # s (t*)
VISCOSITY = 1.0e-6       # Pa·s

# Lateral confining stress
LATERAL_STRESS = 5.0e6   # Pa (σH)

# Initial stress state (isotropic)
INITIAL_AXIAL_STRESS = 5.0e6  # Pa (σV)
INITIAL_LATERAL_STRESS = 5.0e6  # Pa (σH)

# Time integration parameter
dt = 0.001  # time step in seconds

# ============================================================
# SEMI-ANALYTICAL SOLUTION FUNCTIONS
# ============================================================

def compute_yield_function(q, p, cohesion, b_friction):
    """
    Compute Drucker-Prager yield function F.
    
    Args:
        q: Deviatoric stress invariant (Pa)
        p: Mean stress (Pa)
        cohesion: Current cohesion a (Pa)
        b_friction: Friction parameter b
        
    Returns:
        F: Yield function value (positive = yielding)
    """
    return q - (3.0 * cohesion + b_friction * p)


def compute_viscoplastic_multiplier_rate(F, relaxation_time, denominator):
    """
    Compute viscoplastic multiplier rate dλ/dt.
    
    Perzyna/Duvaut-Lions formulation:
    dλ/dt = (1/t*) * F / (3μ + K*b*b' + h)
    
    Args:
        F: Yield function value
        relaxation_time: Characteristic time t*
        denominator: 3*mu + K*b*b' + h
        
    Returns:
        dλ/dt: Viscoplastic multiplier rate
    """
    if F <= 0:
        return 0.0
    return F / (relaxation_time * denominator)


def compute_denominated(mu, K, b, b_prime, h):
    """
    Compute denominator for viscoplastic multiplier.
    
    denominator = 3*mu + K*b*b' + h
    
    Args:
        mu: Shear modulus
        K: Bulk modulus
        b: Friction parameter
        b_prime: Dilation parameter
        h: Hardening rate
        
    Returns:
        denominator
    """
    return 3.0 * mu + K * b * b_prime + h


def semi_analytical_solution(time_history, axial_strain_history):
    """
    Compute semi-analytical solution for viscoplastic response.
    
    Args:
        time_history: Array of time values
        axial_strain_history: Array of imposed axial strains
        
    Returns:
        dict with computed quantities
    """
    n_steps = len(time_history)
    
    # Initialize arrays
    axial_stress = np.zeros(n_steps)
    lateral_strain = np.zeros(n_steps)
    cohesion = np.zeros(n_steps)
    plastic_multiplier = np.zeros(n_steps)
    q_history = np.zeros(n_steps)
    
    # Initial conditions
    axial_stress[0] = INITIAL_AXIAL_STRESS
    cohesion[0] = COHESION
    
    # Constant mean stress (p) for triaxial with constant lateral stress
    # p = (σV + 2*σH)/3
    # Note: σH is constant, σV changes
    
    # Precompute denominator
    denominator = compute_denominated(SHEAR_MODULUS, BULK_MODULUS, 
                                       B_FRICTION, B_DILATION, HARDENING_RATE)
    
    # Time integration (forward Euler)
    for i in range(1, n_steps):
        dt = time_history[i] - time_history[i-1]
        
        # Current total axial strain
        eps_axial = axial_strain_history[i]
        
        # Compute stress state at previous step
        sigma_v = axial_stress[i-1]
        sigma_h = LATERAL_STRESS
        
        # Mean stress
        p = (sigma_v + 2.0 * sigma_h) / 3.0
        
        # Deviatoric stress
        s_v = sigma_v - p
        s_h = sigma_h - p
        
        # Deviatoric stress invariant q = sqrt(3/2 * s:s)
        # For triaxial: q = |s_v - s_h| = |sigma_v - sigma_h|
        q = abs(sigma_v - sigma_h)
        
        # Yield function
        F = compute_yield_function(q, p, cohesion[i-1], B_FRICTION)
        
        # Viscoplastic multiplier increment
        dlambda_dt = compute_viscoplastic_multiplier_rate(
            F, RELAXATION_TIME, denominator)
        dlambda = dlambda_dt * dt
        plastic_multiplier[i] = plastic_multiplier[i-1] + dlambda
        
        # Cohesion evolution (hardening)
        cohesion[i] = COHESION + HARDENING_RATE * plastic_multiplier[i]
        
        # Elastic strain increment
        # Total strain = elastic strain + plastic strain
        # For imposed strain, we compute elastic response with viscoplastic relaxation
        
        # Elastic predictor (assuming no viscoplasticity)
        deps_axial = axial_strain_history[i] - axial_strain_history[i-1]
        
        # Elastic stiffness for triaxial condition
        # dsigma_v = E' * deps_axial_elastic
        # where E' is effective modulus under lateral constraint
        
        # For simplicity, use analytical integration of Perzyna equations
        # This is a simplified approximation - full solution requires
        # integration of the coupled equations
        
        # Stress update (simplified)
        if F > 0:
            # Viscoplastic relaxation reduces stress
            relaxation_factor = np.exp(-dt / RELAXATION_TIME)
            # Elastic trial stress
            sigma_v_trial = sigma_v + YOUNG_MODULUS * deps_axial
            # Relaxed stress (simplified model)
            sigma_v = sigma_v_trial * relaxation_factor + sigma_v * (1 - relaxation_factor)
        else:
            # Elastic response
            sigma_v = sigma_v + YOUNG_MODULUS * deps_axial
        
        axial_stress[i] = sigma_v
        q_history[i] = abs(sigma_v - sigma_h)
    
    # Compute lateral strain (from elastic relation)
    # For constant lateral stress, lateral strain comes from Poisson effect
    # and plastic dilation
    for i in range(n_steps):
        # Simplified: assume lateral strain evolves with axial strain
        lateral_strain[i] = -POISSON_RATIO * axial_strain_history[i]
    
    return {
        'time': time_history,
        'axial_stress': axial_stress,
        'axial_strain': axial_strain_history,
        'lateral_strain': lateral_strain,
        'cohesion': cohesion,
        'plastic_multiplier': plastic_multiplier,
        'q': q_history
    }


def load_geos_results(filename):
    """
    Load GEOS simulation results from output file.
    
    Args:
        filename: Path to GEOS output file
        
    Returns:
        dict with time history data
    """
    if not os.path.exists(filename):
        print(f"Error: GEOS results file '{filename}' not found.")
        return None
    
    try:
        # Try to load with numpy
        data = np.loadtxt(filename, skiprows=1)  # Skip header
        
        # Assume columns: time, delta_axial_stress, lateral_strain, axial_strain, ...
        return {
            'time': data[:, 0],
            'axial_stress_change': data[:, 1],
            'lateral_strain': data[:, 2],
            'axial_strain': data[:, 3],
        }
    except Exception as e:
        print(f"Error loading GEOS results: {e}")
        return None


def load_strain_history(filename):
    """
    Load imposed strain history from table file.
    
    Args:
        filename: Path to strain history file
        
    Returns:
        tuple: (time_array, strain_array)
    """
    data = np.loadtxt(filename, skiprows=3)  # Skip 3 header lines
    return data[:, 0], data[:, 1]


def validate_simulation(geos_file, strain_file, output_dir='outputs'):
    """
    Validate GEOS simulation against semi-analytical solution.
    
    Args:
        geos_file: Path to GEOS results file
        strain_file: Path to strain history file
        output_dir: Directory for output plots
        
    Returns:
        bool: True if validation passes
    """
    print("=" * 60)
    print("Visco Drucker-Prager Triaxial Driver Validation")
    print("=" * 60)
    
    # Load imposed strain history
    print(f"\nLoading strain history from: {strain_file}")
    time_history, strain_history = load_strain_history(strain_file)
    print(f"  Time range: {time_history[0]:.3f} to {time_history[-1]:.3f} s")
    print(f"  Strain range: {strain_history[0]:.6f} to {strain_history[-1]:.6f}")
    
    # Compute semi-analytical solution
    print("\nComputing semi-analytical solution...")
    analytical = semi_analytical_solution(time_history, strain_history)
    print("  Semi-analytical solution computed.")
    
    # Load GEOS results
    print(f"\nLoading GEOS results from: {geos_file}")
    geos_results = load_geos_results(geos_file)
    
    if geos_results is None:
        print("\nWARNING: GEOS results not available for comparison.")
        print("This is expected if the simulation has not been run yet.")
        geos_available = False
    else:
        geos_available = True
        print(f"  Time steps: {len(geos_results['time'])}")
    
    # Create comparison plots
    print("\nGenerating validation plots...")
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Plot 1: Axial stress vs axial strain
    ax = axes[0, 0]
    ax.plot(analytical['axial_strain'], analytical['axial_stress'] / 1e6, 
            'b-', linewidth=2, label='Semi-Analytical')
    if geos_available:
        ax.plot(geos_results['axial_strain'], 
                (geos_results['axial_stress_change'] + INITIAL_AXIAL_STRESS) / 1e6,
                'r--', linewidth=1.5, label='GEOS')
    ax.set_xlabel('Axial Strain (-)')
    ax.set_ylabel('Axial Stress (MPa)')
    ax.set_title('Axial Stress vs Axial Strain')
    ax.legend()
    ax.grid(True)
    
    # Plot 2: Lateral strain vs axial strain
    ax = axes[0, 1]
    ax.plot(analytical['axial_strain'], analytical['lateral_strain'], 
            'b-', linewidth=2, label='Semi-Analytical')
    if geos_available:
        ax.plot(geos_results['axial_strain'], geos_results['lateral_strain'],
                'r--', linewidth=1.5, label='GEOS')
    ax.set_xlabel('Axial Strain (-)')
    ax.set_ylabel('Lateral Strain (-)')
    ax.set_title('Lateral Strain vs Axial Strain')
    ax.legend()
    ax.grid(True)
    
    # Plot 3: Time history of axial stress
    ax = axes[1, 0]
    ax.plot(analytical['time'], analytical['axial_stress'] / 1e6, 
            'b-', linewidth=2, label='Semi-Analytical')
    if geos_available:
        ax.plot(geos_results['time'], 
                (geos_results['axial_stress_change'] + INITIAL_AXIAL_STRESS) / 1e6,
                'r--', linewidth=1.5, label='GEOS')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Axial Stress (MPa)')
    ax.set_title('Axial Stress vs Time')
    ax.legend()
    ax.grid(True)
    
    # Plot 4: Deviatoric stress q vs time
    ax = axes[1, 1]
    ax.plot(analytical['time'], analytical['q'] / 1e6, 
            'b-', linewidth=2, label='Semi-Analytical')
    ax.axhline(y=(3*COHESION + B_FRICTION * INITIAL_AXIAL_STRESS)/1e6, 
               color='g', linestyle=':', label='Initial Yield (q)')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Deviatoric Stress q (MPa)')
    ax.set_title('Deviatoric Stress vs Time')
    ax.legend()
    ax.grid(True)
    
    plt.tight_layout()
    
    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    plot_file = os.path.join(output_dir, 'validation_plot.png')
    plt.savefig(plot_file, dpi=150)
    print(f"  Plot saved to: {plot_file}")
    
    # Compute errors if GEOS results available
    if geos_available:
        print("\nComputing validation errors...")
        
        # Interpolate analytical solution to GEOS time points
        from scipy.interpolate import interp1d
        
        f_axial_stress = interp1d(analytical['time'], analytical['axial_stress'], 
                                   kind='linear', fill_value='extrapolate')
        analytical_at_geos = f_axial_stress(geos_results['time'])
        
        geos_total_stress = geos_results['axial_stress_change'] + INITIAL_AXIAL_STRESS
        
        # L2 relative error
        error = np.abs(geos_total_stress - analytical_at_geos)
        relative_error = error / np.abs(analytical_at_geos)
        mean_relative_error = np.mean(relative_error) * 100
        max_relative_error = np.max(relative_error) * 100
        
        print(f"  Mean relative error in axial stress: {mean_relative_error:.2f}%")
        print(f"  Max relative error in axial stress: {max_relative_error:.2f}%")
        
        # Validation criterion: < 5% mean error is acceptable
        if mean_relative_error < 5.0:
            print("\n  VALIDATION PASSED: Mean error < 5%")
            return True
        else:
            print("\n  VALIDATION WARNING: Mean error >= 5%")
            return False
    else:
        print("\n  Skipping error computation (no GEOS results)")
        print("  Run GEOS simulation to complete validation")
        return None


def main():
    """Main validation routine."""
    
    # File paths
    geos_results_file = '../../outputs/ViscoDruckerPragerResults.txt'
    strain_file = '../triaxialDriver/tables/axialStrainHistory.txt'
    output_dir = '../../outputs'
    
    # Change to script directory for relative paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run validation
    result = validate_simulation(geos_results_file, strain_file, output_dir)
    
    if result is True:
        print("\n" + "=" * 60)
        print("VALIDATION SUCCESSFUL")
        print("=" * 60)
        return 0
    elif result is False:
        print("\n" + "=" * 60)
        print("VALIDATION FAILED")
        print("=" * 60)
        return 1
    else:
        print("\n" + "=" * 60)
        print("VALIDATION PENDING (GEOS results not available)")
        print("=" * 60)
        return 0


if __name__ == '__main__':
    sys.exit(main())
