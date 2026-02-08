# Visco Drucker-Prager Triaxial Driver Simulation

## Overview

This simulation validates the Visco Drucker-Prager constitutive model in GEOS using the Triaxial Driver solver. The test performs a material point simulation with imposed axial strain loading/unloading cycles and constant lateral confining stress.

## File Structure

```
inputs/triaxialDriver/
├── triaxialDriver_ViscoDruckerPrager.xml   # Main driver file (Task definition)
├── triaxialDriver_base.xml                 # Base file (constitutive model)
├── tables/
│   └── axialStrainHistory.txt            # Loading history table
└── scripts/
    └── validate_visco_drucker_prager.py    # Validation script

outputs/
├── ViscoDruckerPragerResults.txt           # GEOS output (after simulation)
└── validation_plot.png                     # Validation plots (after analysis)
```

## Material Parameters

### Elastic Properties
- Bulk modulus (K): 3.333 GPa
- Shear modulus (μ): 2.0 GPa
- Young's modulus (E): 5.0 GPa (derived)
- Poisson's ratio (ν): 0.25 (derived)

### Drucker-Prager Yield Surface
- Friction angle: 30° (b = 6sinφ/(3-sinφ) ≈ 1.1547)
- Initial cohesion (a): 1.0 MPa

### Plastic Potential
- Dilation angle: 20° (b' ≈ 0.8165)

### Hardening
- Hardening rate (h): 500 MPa

### Viscoplastic Parameters
- Relaxation time (t*): 1.0 s
- Viscosity: 1.0e-6 Pa·s

### Other
- Density: 2700 kg/m³
- Lateral confining stress (σH): 5.0 MPa
- Initial stress state: Isotropic at 5.0 MPa

## Loading Protocol

The axial strain follows a piecewise linear history with:
- Loading phases (compression): strain becomes more negative
- Unloading phases: strain returns toward zero
- Multiple cycles to test yielding in both positive and negative q regimes

## Running the Simulation

1. Ensure GEOS is compiled and available in your PATH
2. Run the simulation:
   ```bash
   cd inputs/triaxialDriver
   geos triaxialDriver_ViscoDruckerPrager.xml
   ```

3. Results will be written to `outputs/ViscoDruckerPragerResults.txt`

## Running Validation

After the simulation completes:

```bash
cd inputs/triaxialDriver/scripts
python3 validate_visco_drucker_prager.py
```

This will:
- Load the GEOS results
- Compute the semi-analytical Perzyna solution
- Generate comparison plots
- Calculate validation errors

## Theory

### Drucker-Prager Yield Function

The yield surface is defined as:
```
F = q - (3a + b*p)
```

where:
- q = √(3/2 s:s) is the deviatoric stress invariant
- p = (1/3) tr(σ) is the mean stress
- a is the cohesion parameter
- b is the friction parameter

### Viscoplastic Flow Rule

The Duvaut-Lions viscoplastic formulation (equivalent to Perzyna for linear hardening):

```
dλ/dt = (1/t*) × F / (3μ + K×b×b' + h)
```

where:
- t* is the relaxation time
- μ is the shear modulus
- K is the bulk modulus
- b' is the dilation parameter
- h is the hardening rate

### Stress Update

The stress evolves according to:
- Elastic predictor: σ_trial = σ_n + C:Δε
- Viscoplastic relaxation if F > 0
- Stress update depends on sign of shear stress q

## Output Format

The output file `ViscoDruckerPragerResults.txt` contains:
- Time (s)
- Change in axial stress Δσv (Pa)
- Lateral strain εh (-)
- Axial strain εv (-)
- Plastic multiplier λ
- Cohesion a (Pa)

## References

1. Perzyna, P. (1966). "Fundamental problems in viscoplasticity." Advances in Applied Mechanics, 9, 243-377.
2. Duvaut, G. and Lions, J.L. (1976). "Inequalities in Mechanics and Physics." Springer.
3. GEOS Documentation: Visco Drucker-Prager Model
