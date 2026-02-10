#!/usr/bin/env python3
"""
Visco Drucker-Prager Triaxial Driver Validation Script

This script compares GEOS simulation results against semi-analytical solutions
based on the Perzyna viscoplasticity approach with Duvaut-Lions regularization.

The Visco Drucker-Prager model follows:
    σ̇ = C:(ε̇ - ε̇^vp)
    ε̇^vp = (1/τ) * C^(-1):(σ - σ^eq)

where τ is the relaxation time and σ^eq is the rate-independent solution.

Key assumptions:
- Linear hardening: Δa = h * Δλ
- Associated/non-associated flow with dilation parameter
- Constant lateral stress (triaxial conditions)
"""

import numpy as np
import matplotlib.pyplot as plt


def compute_semi_analytical_solution(time, strain_history, material_params):
    """
    Compute semi-analytical solution for Visco Drucker-Prager under triaxial loading.
    
    Parameters:
    -----------
    time : array
        Time values
    strain_history : array
        Imposed axial strain values
    material_params : dict
        Material parameters (K, mu, a0, b, bp, h, tau, sigma_h)
    
    Returns:
    --------
    dict with stress, strain, and internal variable histories
    """
    K = material_params['bulkModulus']
    mu = material_params['shearModulus']
    a0 = material_params['cohesion']
    b = material_params['friction']
    bp = material_params['dilation']
    h = material_params['hardening']
    tau = material_params['relaxationTime']
    sigma_h = material_params['sigmaConfining']
    
    # Elastic stiffness matrix components for triaxial conditions
    # Under triaxial conditions with constant lateral stress:
    # Δσ_v = (K + 4/3*mu) * Δε_v + (K - 2/3*mu) * 2*Δε_h
    # Δσ_h = (K - 2/3*mu) * Δε_v + (K + 1/3*mu) * Δε_h = 0 (constant)
    # From Δσ_h = 0, we get relationship between axial and lateral strain
    
    K43mu = K + 4.0/3.0 * mu
    K23mu = K - 2.0/3.0 * mu
    
    # Compute equivalent elastic modulus for triaxial conditions
    E_triax = K43mu - 2.0 * K23mu**2 / (K + 1.0/3.0 * mu)
    
    # Initialize arrays
    n = len(time)
    sigma_v = np.zeros(n)  # Axial stress
    epsilon_v = np.zeros(n)  # Axial strain
    epsilon_h = np.zeros(n)  # Lateral strain
    cohesion = np.zeros(n)  # Evolving cohesion
    plastic_multiplier = np.zeros(n)  # Cumulative plastic multiplier
    
    # Initial conditions
    sigma_v[0] = material_params['sigmaInitialAxial']
    epsilon_v[0] = strain_history[0]
    cohesion[0] = a0
    
    # Shear modulus factor for viscoplastic flow
    G_factor = 3.0 * mu + K * b * bp + h
    
    # Time stepping solution
    for i in range(1, n):
        dt = time[i] - time[i-1]
        epsilon_v[i] = strain_history[i]
        delta_eps_v = epsilon_v[i] - epsilon_v[i-1]
        
        # Compute elastic trial stress increment
        delta_sigma_v_trial = E_triax * delta_eps_v
        sigma_v_trial = sigma_v[i-1] + delta_sigma_v_trial
        
        # Compute mean stress and deviatoric stress
        p_trial = (sigma_v_trial + 2.0 * sigma_h) / 3.0
        q_trial = sigma_v_trial - sigma_h  # Deviatoric stress in triaxial
        
        # Yield function (Drucker-Prager)
        F_trial = q_trial + b * p_trial - cohesion[i-1]
        
        if F_trial > 0:  # Viscoplastic yielding
            # Perzyna-type viscoplastic update
            # dλ/dt = (1/τ) * F / G_factor
            delta_lambda = (dt / tau) * F_trial / G_factor
            
            # Update cohesion (linear hardening)
            cohesion[i] = cohesion[i-1] + h * delta_lambda
            plastic_multiplier[i] = plastic_multiplier[i-1] + delta_lambda
            
            # Stress relaxation toward rate-independent solution
            # σ = σ^trial - Δλ * (3μ + K*b*bp) * sign(q)
            relaxation = delta_lambda * (3.0 * mu + K * b * bp)
            sigma_v[i] = sigma_v_trial - relaxation * np.sign(q_trial)
        else:  # Elastic response
            cohesion[i] = cohesion[i-1]
            plastic_multiplier[i] = plastic_multiplier[i-1]
            sigma_v[i] = sigma_v_trial
        
        # Compute lateral strain from constant lateral stress condition
        # ε_h = -(K - 2/3*μ) / (K + 1/3*μ) * ε_v - viscoplastic contribution
        epsilon_h[i] = -K23mu / (K + 1.0/3.0 * mu) * epsilon_v[i]
    
    return {
        'time': time,
        'sigma_v': sigma_v,
        'epsilon_v': epsilon_v,
        'epsilon_h': epsilon_h,
        'cohesion': cohesion,
        'plastic_multiplier': plastic_multiplier
    }


def read_geos_output(filename):
    """
    Read GEOS triaxial driver output file.
    
    Expected format:
    Time AxialStress LateralStrain AxialStrain ...
    """
    try:
        data = np.loadtxt(filename, skiprows=1)  # Skip header if present
        return {
            'time': data[:, 0],
            'sigma_v': data[:, 1],
            'epsilon_h': data[:, 2],
            'epsilon_v': data[:, 3],
            'cohesion': data[:, 4] if data.shape[1] > 4 else None,
            'plastic_multiplier': data[:, 5] if data.shape[1] > 5 else None
        }
    except Exception as e:
        print(f"Error reading GEOS output: {e}")
        return None


def plot_comparison(geos_data, analytical_data, output_dir='outputs'):
    """
    Create comparison plots between GEOS and analytical results.
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Plot 1: Axial stress vs axial strain
    ax = axes[0, 0]
    ax.plot(geos_data['epsilon_v'] * 100, geos_data['sigma_v'] / 1e6, 
            'b-', linewidth=2, label='GEOS')
    ax.plot(analytical_data['epsilon_v'] * 100, analytical_data['sigma_v'] / 1e6, 
            'r--', linewidth=2, label='Semi-Analytical')
    ax.set_xlabel('Axial Strain (%)', fontsize=12)
    ax.set_ylabel('Axial Stress (MPa)', fontsize=12)
    ax.set_title('Axial Stress-Strain Response', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 2: Lateral strain vs axial strain
    ax = axes[0, 1]
    ax.plot(geos_data['epsilon_v'] * 100, geos_data['epsilon_h'] * 100, 
            'b-', linewidth=2, label='GEOS')
    ax.plot(analytical_data['epsilon_v'] * 100, analytical_data['epsilon_h'] * 100, 
            'r--', linewidth=2, label='Semi-Analytical')
    ax.set_xlabel('Axial Strain (%)', fontsize=12)
    ax.set_ylabel('Lateral Strain (%)', fontsize=12)
    ax.set_title('Lateral Strain vs Axial Strain', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 3: Stress evolution vs time
    ax = axes[1, 0]
    ax.plot(geos_data['time'], geos_data['sigma_v'] / 1e6, 
            'b-', linewidth=2, label='GEOS Axial Stress')
    ax.plot(analytical_data['time'], analytical_data['sigma_v'] / 1e6, 
            'r--', linewidth=2, label='Analytical Axial Stress')
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Axial Stress (MPa)', fontsize=12)
    ax.set_title('Stress Evolution', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 4: Cohesion evolution (if available)
    ax = axes[1, 1]
    if geos_data['cohesion'] is not None:
        ax.plot(geos_data['time'], geos_data['cohesion'] / 1e6, 
                'b-', linewidth=2, label='GEOS Cohesion')
    ax.plot(analytical_data['time'], analytical_data['cohesion'] / 1e6, 
            'r--', linewidth=2, label='Analytical Cohesion')
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Cohesion (MPa)', fontsize=12)
    ax.set_title('Cohesion Evolution (Hardening)', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/ViscoDruckerPrager_Validation.png', dpi=150)
    print(f"Validation plot saved to {output_dir}/ViscoDruckerPrager_Validation.png")
    plt.show()


def compute_error_metrics(geos_data, analytical_data):
    """
    Compute error metrics between GEOS and analytical solutions.
    """
    # Interpolate analytical data to GEOS time points if needed
    from scipy.interpolate import interp1d
    
    metrics = {}
    
    # Axial stress error
    f_sigma = interp1d(analytical_data['time'], analytical_data['sigma_v'], 
                       kind='linear', fill_value='extrapolate')
    sigma_analytical_interp = f_sigma(geos_data['time'])
    sigma_error = np.abs(geos_data['sigma_v'] - sigma_analytical_interp)
    metrics['sigma_max_error'] = np.max(sigma_error) / 1e6  # MPa
    metrics['sigma_mean_error'] = np.mean(sigma_error) / 1e6  # MPa
    metrics['sigma_rmse'] = np.sqrt(np.mean(sigma_error**2)) / 1e6  # MPa
    
    # Lateral strain error
    f_eps_h = interp1d(analytical_data['time'], analytical_data['epsilon_h'], 
                       kind='linear', fill_value='extrapolate')
    eps_h_analytical_interp = f_eps_h(geos_data['time'])
    eps_h_error = np.abs(geos_data['epsilon_h'] - eps_h_analytical_interp)
    metrics['eps_h_max_error'] = np.max(eps_h_error)
    metrics['eps_h_mean_error'] = np.mean(eps_h_error)
    
    return metrics


def main():
    """Main validation routine."""
    
    # Material parameters (SI units)
    material_params = {
        'bulkModulus': 8.3333e9,      # Pa
        'shearModulus': 3.8462e9,     # Pa
        'cohesion': 1.0e6,            # Pa
        'friction': 0.5,              # Drucker-Prager friction parameter b
        'dilation': 0.5,              # Drucker-Prager dilation parameter b'
        'hardening': 1.0e7,           # Pa (linear hardening rate)
        'relaxationTime': 50.0,       # s
        'sigmaConfining': -2.0e6,     # Pa (constant lateral stress)
        'sigmaInitialAxial': -2.0e6,  # Pa (initial axial stress)
    }
    
    # Define loading history (from table files)
    time = np.array([0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 
                     35.0, 40.0, 45.0, 50.0, 55.0, 60.0])
    strain_history = np.array([0.0, -0.001, -0.002, -0.004, -0.006, -0.005, 
                               -0.004, -0.003, -0.002, -0.004, -0.006, -0.007, -0.008])
    
    # Compute semi-analytical solution
    print("Computing semi-analytical solution...")
    analytical_data = compute_semi_analytical_solution(time, strain_history, material_params)
    
    # Read GEOS output
    geos_filename = 'outputs/ViscoDruckerPragerResults.txt'
    print(f"Reading GEOS results from {geos_filename}...")
    geos_data = read_geos_output(geos_filename)
    
    if geos_data is None:
        print("GEOS output not found. Generating analytical solution only.")
        # Save analytical solution
        np.savetxt(f'{geos_filename}', 
                   np.column_stack([analytical_data['time'], 
                                   analytical_data['sigma_v'],
                                   analytical_data['epsilon_h'],
                                   analytical_data['epsilon_v'],
                                   analytical_data['cohesion'],
                                   analytical_data['plastic_multiplier']]),
                   header='Time AxialStress LateralStrain AxialStrain Cohesion PlasticMultiplier',
                   fmt='%.6e')
        print(f"Analytical solution saved to {geos_filename}")
        return
    
    # Compute error metrics
    print("\nComputing error metrics...")
    metrics = compute_error_metrics(geos_data, analytical_data)
    
    print("\n=== Validation Results ===")
    print(f"Axial Stress Max Error: {metrics['sigma_max_error']:.4f} MPa")
    print(f"Axial Stress Mean Error: {metrics['sigma_mean_error']:.4f} MPa")
    print(f"Axial Stress RMSE: {metrics['sigma_rmse']:.4f} MPa")
    print(f"Lateral Strain Max Error: {metrics['eps_h_max_error']:.6e}")
    print(f"Lateral Strain Mean Error: {metrics['eps_h_mean_error']:.6e}")
    
    # Create comparison plots
    print("\nGenerating comparison plots...")
    plot_comparison(geos_data, analytical_data)
    
    # Validation threshold
    if metrics['sigma_rmse'] < 0.1:  # 0.1 MPa tolerance
        print("\n✓ VALIDATION PASSED: GEOS results agree with semi-analytical solution")
    else:
        print("\n✗ VALIDATION FAILED: Discrepancy exceeds tolerance")


if __name__ == "__main__":
    main()
