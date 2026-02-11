# Non-Linear Thermal Diffusion Around a Wellbore
## Temperature-Dependent Volumetric Heat Capacity Case

### Simulation Summary

This directory contains the results of a non-linear thermal diffusion simulation around a wellbore, where the volumetric heat capacity of the rock varies linearly with temperature.

---

## Configuration Files

### Base File: `inputs/nonLinearThermalDiffusion_wellbore_base.xml`

This file contains the core physics setup:

- **Solver**: `SinglePhaseFVM` with thermal effects enabled (`isThermal="1"`)
- **Non-linear Solver Parameters**:
  - Newton tolerance: 1.0e-6
  - Maximum Newton iterations: 100
  
- **Constitutive Models**:
  - `SolidInternalEnergy` with temperature-dependent heat capacity
    - Reference volumetric heat capacity: 4.56e6 J/(m³·K)
    - dVolumetricHeatCapacity/dTemperature: 1e6 J/(m³·K²)
  - `ThermalCompressibleSinglePhaseFluid` for fluid properties
  - `SinglePhaseThermalConductivity` for thermal conduction
  - `CompressibleSolidConstantPermeability` for rock properties

### Benchmark File: `inputs/nonLinearThermalDiffusion_temperatureDependentVolumetricHeatCapacity_benchmark.xml`

This file defines the specific case:

- **Mesh**: InternalWellbore generator
  - Wellbore radius: 0.1 m
  - Far-field radius: 5.0 m
  - Radial elements: 100 (with automatic grading)
  - Angular elements: 40
  
- **Boundary Conditions**:
  - Initial temperature: 100 (relative scale)
  - Wellbore temperature: -20 (cold injection)
  - Far-field temperature: 100 (constant)
  
- **Simulation Time**: 1000 seconds with adaptive timestepping

---

## Material Properties

| Property | Value | Units |
|----------|-------|-------|
| Reference volumetric heat capacity (Cv,ref) | 4.56×10⁶ | J/(m³·K) |
| Temperature derivative of Cv (dCv/dT) | 1×10⁶ | J/(m³·K²) |
| Thermal conductivity (k) | 1.66 | W/(m·K) |
| Porosity (φ) | 0.1 | - |
| Permeability | 1×10⁻¹⁸ | m² |
| Fluid density | 1000 | kg/m³ |
| Fluid compressibility | 5×10⁻¹⁰ | 1/Pa |

---

## Simulation Results

### Convergence Statistics

From the GEOS output:

| Metric | Value |
|--------|-------|
| Total time steps | 23 |
| Time step cuts | 0 |
| Successful nonlinear iterations | 59 |
| Successful linear iterations | 59 |
| Discarded iterations | 0 |

The simulation converged successfully with no time step cuts, indicating stable time-stepping and good convergence of the non-linear iterations.

### Output Files

- **VTK Output**: `vtkOutput/` directory containing time-dependent temperature fields
- **Restart Files**: HDF5 format for checkpointing
- **PVD File**: ParaView data file for visualization

---

## Physics Description

### Temperature-Dependent Volumetric Heat Capacity

The key non-linearity in this simulation comes from the temperature-dependent volumetric heat capacity:

```
Cv(T) = Cv,ref + (dCv/dT) × (T - Tref)
```

Where:
- Cv(T) = volumetric heat capacity at temperature T
- Cv,ref = 4.56×10⁶ J/(m³·K) at Tref = 0
- dCv/dT = 1×10⁶ J/(m³·K²)

This linear dependence introduces non-linearity into the thermal diffusion equation, requiring Newton iterations for solution.

### Governing Equation

The thermal diffusion equation with temperature-dependent heat capacity:

```
ρ·Cv(T)·∂T/∂t = ∇·(k·∇T)
```

Where the left side contains the non-linear term due to Cv(T).

---

## Visualization

### Python Script: `inputs/scripts/plot_temperature_profiles.py`

The visualization script generates:
1. Temperature vs radial distance at multiple time steps
2. Comparison plots (early vs late time)
3. Temperature evolution at specific radii
4. Temperature gradient analysis
5. Data export to text format

**Note**: The script requires the `vtk` Python module:
```bash
pip install vtk
```

### Viewing Results in ParaView

1. Open `outputs/vtkOutput/vtkOutput.pvd` in ParaView
2. Select temperature field for visualization
3. Use animation controls to view time evolution
4. Create line plots for radial temperature profiles

---

## Validation

This simulation can be validated against:

1. **Classical finite difference solutions** for non-linear thermal diffusion
2. **Analytical solutions** for linear case (when dCv/dT = 0)
3. **Comparisons with the linear thermal diffusion benchmark** (see `rock_linear` material model in base file)

The expected behavior:
- Temperature propagates outward from wellbore
- Non-linearity causes asymmetric temperature profiles compared to linear case
- Convergence requires more iterations than linear case

---

## Running the Simulation

```bash
# Run the benchmark
cd /home/brianliu/geophysics_agent/data/eval/experiments_subset/AdvancedWellboreExampleNonLinearThermalDiffusionTemperatureDependentVolumetricHeatCapacity
geosx -i inputs/nonLinearThermalDiffusion_temperatureDependentVolumetricHeatCapacity_benchmark.xml

# Generate visualizations
python3 inputs/scripts/plot_temperature_profiles.py
```

---

## File Structure

```
workspace/
├── inputs/
│   ├── nonLinearThermalDiffusion_wellbore_base.xml
│   ├── nonLinearThermalDiffusion_temperatureDependentVolumetricHeatCapacity_benchmark.xml
│   └── scripts/
│       └── plot_temperature_profiles.py
├── outputs/
│   ├── vtkOutput/              # VTK output files
│   ├── *_restart_*/            # Restart files
│   └── README_simulation_summary.md
└── README.md
```

---

## References

This example is based on the GEOS validation study:
- **Documentation**: `nonLinearThermalDiffusion_TemperatureDependentVolumetricHeatCapacity/Example.rst`
- **Base file**: `inputFiles/singlePhaseFlow/thermalCompressible_2d_base.xml`

---

## Contact & Support

For questions about this example, please submit a GitHub issue on the GEOS project page:
https://github.com/GEOS-DEV/GEOS/issues
