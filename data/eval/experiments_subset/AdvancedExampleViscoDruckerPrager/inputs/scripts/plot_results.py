#!/usr/bin/env python3
"""
Visco Drucker-Prager Triaxial Driver Results Visualization and Validation

This script:
1. Loads GEOS Triaxial Driver results
2. Computes semi-analytical solutions based on Perzyna viscoplasticity theory
3. Generates comparison plots between numerical and analytical results

Usage:
    python inputs/scripts/plot_results.py [--geosDir <path>] [--outputDir <path>]

References:
    Runesson et al. (1999) - Perzyna time-dependent approach
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ElementTree
import argparse


def load_geos_results(output_dir):
    """Load GEOS Triaxial Driver results from text file."""
    path = os.path.join(output_dir, "ViscoDruckerPragerResults.txt")
    time, ax_strain, ra_strain1, ra_strain2, ax_stress, ra_stress1, ra_stress2, \
        newton_iter, residual_norm = np.loadtxt(path, skiprows=5, unpack=True)
    return time, ax_strain, ra_strain1, ax_stress, ra_stress1


def parse_material_parameters(xml_path, xml_case_path):
    """Extract material parameters from XML files."""
    tree = ElementTree.parse(xml_path)
    tree_case = ElementTree.parse(xml_case_path)
    
    model = tree_case.find('Tasks/TriaxialDriver')
    param = tree.find('Constitutive/ViscoDruckerPrager')

    params = {
        'bulkModulus': float(param.get("defaultBulkModulus")),
        'shearModulus': float(param.get("defaultShearModulus")),
        'cohesion': float(param.get("defaultCohesion")),
        'frictionAngle': float(param.get("defaultFrictionAngle")),
        'dilationAngle': float(param.get("defaultDilationAngle")),
        'hardeningRate': float(param.get("defaultHardeningRate")),
        'relaxationTime': float(param.get("relaxationTime")),
        'initialStress': float(model.get("initialStress"))
    }
    
    return params


def compute_derived_parameters(params):
    """Compute derived elastic and plastic parameters."""
    # Elastic moduli
    lameModulus = params['bulkModulus'] - 2.0/3.0 * params['shearModulus']
    youngModulus = 1.0 / (1.0/9.0/params['bulkModulus'] + 1.0/3.0/params['shearModulus'])
    
    # Friction parameters (Drucker-Prager)
    frictionAngleRad = params['frictionAngle'] * np.pi / 180.0
    cosFrictionAngle = np.cos(frictionAngleRad)
    sinFrictionAngle = np.sin(frictionAngleRad)
    
    # Cohesion parameter 'a'
    a = 6.0 * params['cohesion'] * cosFrictionAngle / (3.0 - sinFrictionAngle)
    
    # Friction parameter 'b'
    b = 6.0 * sinFrictionAngle / (3.0 - sinFrictionAngle)
    
    # Dilation parameter 'b_prime'
    dilationAngleRad = params['dilationAngle'] * np.pi / 180.0
    sinDilationAngle = np.sin(dilationAngleRad)
    b_dilation = 6.0 * sinDilationAngle / (3.0 - sinDilationAngle)
    
    # Elasto-plastic modulus (Runesson et al. 1999, Eq. 56)
    parameter_Aep = (3.0 * params['shearModulus'] + 
                     params['bulkModulus'] * b * b_dilation + 
                     params['hardeningRate'])
    
    return {
        'lameModulus': lameModulus,
        'youngModulus': youngModulus,
        'a': a,
        'b': b,
        'b_dilation': b_dilation,
        'parameter_Aep': parameter_Aep
    }


def compute_semi_analytical_solution(params, derived, time_data, strain_data, stress_data):
    """
    Compute semi-analytical solution using Perzyna viscoplasticity theory.
    
    Based on Runesson et al. (1999):
    - For q >= 0 (loading):
        d_sigma_v = (d_epsilon_v - d_lambda*(b'-3)/3) * E
        d_epsilon_h = d_epsilon_v - d_sigma_v/(2*mu) + 3/2*d_lambda
    - For q < 0 (unloading):
        d_sigma_v = (d_epsilon_v - d_lambda*(b'+3)/3) * E
        d_epsilon_h = d_epsilon_v - d_sigma_v/(2*mu) - 3/2*d_lambda
    
    where d_lambda = (dt/t*) * F / (3*mu + K*b*b' + h)
    """
    n_steps = len(strain_data)
    
    ax_stress_anal = np.zeros(n_steps)
    ra_strain_anal = np.zeros(n_steps)
    
    ax_stress_anal[0] = params['initialStress']
    ra_strain_anal[0] = 0.0
    
    # Copy of cohesion for evolution
    a = derived['a']
    
    for idx in range(1, n_steps):
        dt = time_data[idx] - time_data[idx-1]
        d_epsilon_v = strain_data[idx] - strain_data[idx-1]
        d_sigma_r = 0  # Constant radial confining stress
        
        # Elastic trial
        d_epsilon_r = (d_sigma_r - derived['lameModulus'] * d_epsilon_v) / \
                      (2.0 * derived['lameModulus'] + 2.0 * params['shearModulus'])
        d_sigma_v = ((derived['lameModulus'] + 2.0 * params['shearModulus']) * d_epsilon_v + 
                     derived['lameModulus'] / (derived['lameModulus'] + params['shearModulus']) * 
                     (d_sigma_r - derived['lameModulus'] * d_epsilon_v))
        
        sigma_v = ax_stress_anal[idx-1] + d_sigma_v
        epsilon_r = ra_strain_anal[idx-1] + d_epsilon_r
        
        # Compute stress invariants
        sigma_r = stress_data[idx]
        p = (sigma_v + 2.0 * sigma_r) / 3.0
        q = -(sigma_v - sigma_r)
        
        # Plastic correction (Perzyna viscoplasticity)
        if q >= 0:  # Loading with positive shear stress
            F = q + derived['b'] * p - a
            
            if F >= 0:  # Yielding occurs
                d_lambda = dt / params['relaxationTime'] * (F / derived['parameter_Aep'])
                
                d_sigma_v = (d_epsilon_v - d_lambda * (derived['b_dilation'] - 3.0) / 3.0) * derived['youngModulus']
                d_epsilon_r = d_epsilon_v - d_sigma_v / 2.0 / params['shearModulus'] + 1.5 * d_lambda
                
                sigma_v = ax_stress_anal[idx-1] + d_sigma_v
                epsilon_r = ra_strain_anal[idx-1] + d_epsilon_r
                
                a += params['hardeningRate'] * d_lambda
        else:  # Unloading with negative shear stress
            F = -q + derived['b'] * p - a
            
            if F >= 0:  # Yielding occurs
                d_lambda = dt / params['relaxationTime'] * (F / derived['parameter_Aep'])
                
                d_sigma_v = (d_epsilon_v - d_lambda * (derived['b_dilation'] + 3.0) / 3.0) * derived['youngModulus']
                d_epsilon_r = d_epsilon_v - d_sigma_v / 2.0 / params['shearModulus'] - 1.5 * d_lambda
                
                sigma_v = ax_stress_anal[idx-1] + d_sigma_v
                epsilon_r = ra_strain_anal[idx-1] + d_epsilon_r
                
                a += params['hardeningRate'] * d_lambda
        
        ax_stress_anal[idx] = sigma_v
        ra_strain_anal[idx] = epsilon_r
    
    return ax_stress_anal, ra_strain_anal


def create_plots(time, ax_strain, ra_strain, ax_stress, ax_stress_anal, ra_strain_anal, output_dir):
    """Generate comparison plots between GEOS and semi-analytical results."""
    
    # Compute derived quantities
    p_num = ax_stress  # Simplified - using only available stress
    q_num = -(ax_stress - (-10e6))  # Assuming constant radial stress
    strain_vol = ax_strain + 2.0 * ra_strain
    
    p_anal = ax_stress_anal
    q_anal = -(ax_stress_anal - (-10e6))
    strain_vol_anal = ax_strain + 2.0 * ra_strain_anal
    
    # Visualization parameters
    fsize = 14
    msize = 8
    lw = 3
    malpha = 0.6
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    cmap = plt.get_cmap("tab10")
    
    # Plot 1: Strain vs Deviatoric Stress (q)
    axes[0].plot(-ax_strain * 100, q_num * 1e-6, 'o', color=cmap(0), mec='b',
                 markersize=msize, alpha=malpha, label='Triaxial Driver')
    axes[0].plot(-ra_strain * 100, q_num * 1e-6, 'o', color=cmap(0), mec='b',
                 markersize=msize, alpha=malpha)
    axes[0].plot(-ax_strain * 100, q_anal * 1e-6, '-', color='r', mec='r',
                 markersize=msize, alpha=malpha, label='Semi-Analytical', linewidth=lw)
    axes[0].plot(-ra_strain_anal * 100, q_anal * 1e-6, '-', color='r', mec='r',
                 markersize=msize, alpha=malpha, linewidth=lw)
    axes[0].set_xlabel(r'Strain (%)', size=fsize, weight="bold")
    axes[0].set_ylabel(r'Deviatoric Stress (MPa)', size=fsize, weight="bold")
    axes[0].legend(loc='best', fontsize=fsize-2)
    axes[0].grid(True, alpha=0.3)
    
    # Plot 2: Axial Strain vs Volumetric Strain
    axes[1].plot(-ax_strain * 100, -strain_vol * 100, 'o', color=cmap(0), mec='b',
                 markersize=msize, alpha=malpha, label='Triaxial Driver')
    axes[1].plot(-ax_strain * 100, -strain_vol_anal * 100, '-', color='r', mec='r',
                 markersize=msize, alpha=malpha, label='Semi-Analytical', linewidth=lw)
    axes[1].set_xlabel(r'Axial Strain (%)', size=fsize, weight="bold")
    axes[1].set_ylabel(r'Volumetric Strain (%)', size=fsize, weight="bold")
    axes[1].legend(loc='best', fontsize=fsize-2)
    axes[1].grid(True, alpha=0.3)
    
    # Plot 3: Mean Stress vs Deviatoric Stress (yield surface)
    axes[2].plot(-p_num * 1e-6, q_num * 1e-6, 'o', color=cmap(0), mec='b',
                 markersize=msize, alpha=malpha, label='Triaxial Driver')
    axes[2].plot(-p_anal * 1e-6, q_anal * 1e-6, '-', color='r', mec='r',
                 markersize=msize, alpha=malpha, label='Semi-Analytical', linewidth=lw)
    axes[2].set_xlabel(r'Mean Stress (MPa)', size=fsize, weight="bold")
    axes[2].set_ylabel(r'Deviatoric Stress (MPa)', size=fsize, weight="bold")
    axes[2].legend(loc='best', fontsize=fsize-2)
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    output_path = os.path.join(output_dir, "ViscoDruckerPrager_Comparison.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved figure to: {output_path}")
    
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Visualize and validate Visco Drucker-Prager Triaxial Driver results")
    parser.add_argument('--geosDir', help='Path to the GEOS repository',
                        default='.')
    parser.add_argument('--outputDir', help='Path to output directory',
                        default='outputs')

    args = parser.parse_args()
    
    # File paths
    output_dir = args.outputDir
    geos_dir = args.geosDir
    
    # Load GEOS results
    print("Loading GEOS results...")
    time, ax_strain, ra_strain, ax_stress, ra_stress = load_geos_results(output_dir)
    
    # Parse material parameters
    print("Parsing material parameters...")
    xml_path = os.path.join(geos_dir, "inputs/triaxialDriver_base.xml")
    xml_case_path = os.path.join(geos_dir, "inputs/triaxialDriver_ViscoDruckerPrager.xml")
    
    params = parse_material_parameters(xml_path, xml_case_path)
    derived = compute_derived_parameters(params)
    
    print(f"  Bulk Modulus: {params['bulkModulus']/1e9:.2f} GPa")
    print(f"  Shear Modulus: {params['shearModulus']/1e9:.2f} GPa")
    print(f"  Young Modulus: {derived['youngModulus']/1e9:.2f} GPa")
    print(f"  Relaxation Time: {params['relaxationTime']:.2f} s")
    
    # Compute semi-analytical solution
    print("Computing semi-analytical solution...")
    # Create radial stress array (constant)
    ra_stress_data = np.full_like(time, -10e6)
    ax_stress_anal, ra_strain_anal = compute_semi_analytical_solution(
        params, derived, time, ax_strain, ra_stress_data)
    
    # Generate plots
    print("Generating plots...")
    create_plots(time, ax_strain, ra_strain, ax_stress, ax_stress_anal, ra_strain_anal, output_dir)
    
    # Compute errors
    stress_error = np.abs(ax_stress - ax_stress_anal) / np.maximum(np.abs(ax_stress_anal), 1e-6) * 100
    print(f"\nMaximum stress error: {np.max(stress_error):.2f}%")
    print(f"Mean stress error: {np.mean(stress_error):.2f}%")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
