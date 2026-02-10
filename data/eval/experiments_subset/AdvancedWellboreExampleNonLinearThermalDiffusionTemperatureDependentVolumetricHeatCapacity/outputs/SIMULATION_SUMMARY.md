# Non-Linear Thermal Diffusion Around a Wellbore - Simulation Summary

## Overview

This simulation models **non-linear thermal diffusion** in porous rock surrounding a wellbore, with the key feature of **temperature-dependent volumetric heat capacity**. The problem demonstrates how non-linear material properties affect heat transfer in geothermal and reservoir engineering applications.

## Problem Description

### Physics
- **Thermal compressible single-phase flow** using GEOS's `SinglePhaseFVM` solver with thermal effects enabled
- **Temperature-dependent volumetric heat capacity** introduces non-linearity:
  ```
  Cv(T) = referenceVolumetricHeatCapacity + dVolumetricHeatCapacity_dTemperature × (T - T_ref)
  ```
- The derivative `dVolumetricHeatCapacity_dTemperature` captures how heat capacity changes with temperature, creating a non-linear diffusion problem requiring iterative Newton-Raphson solution

### Geometry
- **2D radial (axisymmetric) domain** around a wellbore
- Inner boundary (wellbore wall): r = 0.1 m
- Outer boundary (far-field): r = 5.0 m
- Angular span: 0-90 degrees (quarter symmetry)
- Mesh: ~4,000 elements with refinement near wellbore

### Boundary Conditions
| Location | Pressure [Pa] | Temperature [°C] |
|----------|---------------|------------------|
| Wellbore wall (rneg) | 0 | -20 |
| Far-field (rpos) | 0 | 100 |

### Initial Conditions
- Uniform pressure: 0 Pa
- Uniform temperature: 100°C

### Material Properties

#### Solid (Rock)
| Property | Value | Unit |
|----------|-------|------|
| Reference volumetric heat capacity | 4.56×10⁶ | J/(m³·K) |
| dVolumetricHeatCapacity/dT | 1.0×10⁶ | J/(m³·K²) |
| Thermal conductivity | 1.5 | W/(m·K) |
| Porosity | 0.1 | - |
| Permeability | 1.0×10⁻¹⁸ | m² |

#### Fluid (Pore Fluid)
| Property | Value | Unit |
|----------|-------|------|
| Density | 1000 | kg/m³ |
| Viscosity | 0.001 | Pa·s |
| Thermal expansion coefficient | 3.0×10⁻⁴ | 1/K |
| Specific heat capacity | 1 | J/(kg·K) |

### Simulation Parameters
- Total time: 100,000 seconds (~27.8 hours)
- Max timestep: 1,000 seconds
- Newton tolerance: 1.0×10⁻⁸
- Output interval: 10,000 seconds

## File Structure

### 1. Base Configuration (`inputs/nonLinearThermalDiffusion_2d_base.xml`)
Contains the reusable physics setup:
- Solver configuration (`SinglePhaseFVM` with `isThermal="1"`)
- Constitutive models including the key `SolidInternalEnergy` model with temperature-dependent heat capacity
- Boundary condition definitions (pressure and temperature on all face boundaries)
- Output configuration

### 2. Benchmark Configuration (`inputs/nonLinearThermalDiffusion_2d_benchmark.xml`)
Contains case-specific parameters:
- Mesh definition using `InternalWellbore` generator
- Element region with material assignments
- Time-stepping and event scheduling

### 3. Visualization Script (`inputs/scripts/plot_thermal_results.py`)
Python script for post-processing that generates:
- Temperature vs radial distance profiles at multiple times
- Temperature evolution at specific radial locations
- Comparison of linear vs non-linear heat capacity effects

## Simulation Results

### Convergence Statistics
```
Time steps: 100
Successful nonlinear iterations: 305
Successful linear iterations: 305
Time step cuts: 0
```

The simulation completed successfully with good convergence behavior - no timestep cuts required.

### Visualization Outputs

The following plots have been generated in the outputs directory:

1. **temperature_radial_profiles.png**: Temperature profiles at t = 0, 10, 20, 50, 100 ks showing the thermal front propagation

2. **temperature_time_evolution.png**: Temperature evolution at r = 0.1, 0.3, 0.5, 1.0, 2.0, 3.0 m showing transient cooling

3. **nonlinear_effect_comparison.png**: Three-panel plot showing:
   - Temperature profile comparison (linear vs non-linear)
   - Volumetric heat capacity variation with radius
   - Effective thermal diffusivity variation

### VTK Output
Time-series VTK files are available for visualization in ParaView:
- Location: `outputs/vtkOutput/`
- Files: `000000.vtm` through `000100.vtm` (11 time snapshots)
- PVD file: `vtkOutput.pvd` (load this in ParaView for time-series)

## Key Features of This Configuration

1. **Non-linear Material Property**: The temperature-dependent volumetric heat capacity (`dVolumetricHeatCapacity_dTemperature`) is the key feature that distinguishes this from a standard linear thermal diffusion problem.

2. **Two-File Organization**: Following GEOS best practices, the configuration uses a base file for physics and a benchmark file for geometry/time-stepping, enabling easy parameter sweeps.

3. **Boundary Condition Consistency**: For thermal single-phase flow, BOTH pressure AND temperature must be specified on all face boundaries.

4. **Mesh Refinement**: The `autoSpaceRadialElems="{1}"` flag enables automatic geometric refinement near the wellbore where temperature gradients are steepest.

## Running the Simulation

```bash
# Run the simulation
geosx -i inputs/nonLinearThermalDiffusion_2d_benchmark.xml

# View results in ParaView
paraview outputs/vtkOutput.pvd

# Generate plots
python inputs/scripts/plot_thermal_results.py
```

## Validation

The generated plots include analytical reference solutions for linear thermal diffusion (constant heat capacity). The GEOS non-linear solution will deviate from these references, particularly:
- Faster heat diffusion near the cold wellbore (lower heat capacity at lower temperatures)
- Slower heat diffusion in the warmer far-field (higher heat capacity at higher temperatures)

This demonstrates the physical effect of temperature-dependent material properties.

## References

This example is based on the GEOS validation study for non-linear thermal diffusion around wellbores with temperature-dependent volumetric heat capacity.
