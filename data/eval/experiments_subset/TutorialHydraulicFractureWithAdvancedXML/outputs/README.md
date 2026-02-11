# GEOS Hydraulic Fracturing Simulation

## Overview

This directory contains a fully-coupled hydraulic fracturing simulation configuration for GEOS (Geomechanics and EOS Simulator). The simulation models the propagation of a single hydraulic fracture within a heterogeneous reservoir with a randomly generated, fractal 1D layer-cake structure.

## Files Created

### Input Files (`inputs/`)

| File | Description |
|------|-------------|
| `hydrofracture_base.xml` | Base configuration file containing solvers, events, constitutive models, functions, numerical methods, element regions, base field specifications, and outputs |
| `hydrofracture_benchmark.xml` | Case-specific file with parameters, mesh definition, geometry, and case-specific boundary conditions |

### Table Files (`inputs/tables/`)

| File | Description |
|------|-------------|
| `x.csv`, `y.csv`, `z.csv` | Coordinate arrays for 3D table functions (1×1×5 layer-cake structure) |
| `sigma_xx.csv`, `sigma_yy.csv`, `sigma_zz.csv` | In-situ stress components per layer (Pa) |
| `bulkModulus.csv`, `shearModulus.csv` | Heterogeneous elastic moduli per layer (Pa) |
| `porePressure.csv` | Initial pore pressure distribution per layer (Pa) |
| `flowRate_time.csv` | Time coordinates for pumping schedule (s) |
| `flowRate.csv` | Normalized flow rate values (0 to 1) |

### Visualization Script (`inputs/scripts/`)

| File | Description |
|------|-------------|
| `plot_hydrofracture_results.py` | Python script for visualizing pumping schedule, geologic model, and mesh configuration |

### Output Files (`outputs/`)

| File | Description |
|------|-------------|
| `pumping_schedule.png` | Injection flow rate vs time |
| `geologic_profile.png` | In-situ stress and elastic moduli profiles |
| `mesh_schematic.png` | X-Y view of mesh with fracture geometry |
| `simulation_summary.txt` | Text summary of simulation setup |

## Key Features

### Advanced XML Capabilities

1. **Parameters with Units**
   ```xml
   <Parameter name="t_max" value="20 [min]"/>
   ```

2. **Symbolic Math Expressions**
   ```xml
   <Parameter name="mu_upscaled" value="`$mu$ * 1.0`"/>
   ```

3. **File Inclusion**
   ```xml
   <Included>
     <File name="hydrofracture_base.xml"/>
   </Included>
   ```

### Physics Coupling

The simulation uses four coupled solvers:

1. **Hydrofracture** - Main coupling solver (gravity in z-direction)
2. **SolidMechanicsLagrangianFEM** - Rock deformation
3. **SinglePhaseFVM** - Fracture fluid flow
4. **SurfaceGenerator** - Fracture propagation

### Mesh Configuration

- **Element type**: C3D8 (hexahedral)
- **X-axis**: 0-200m (uniform) + 200-250m (bias -0.6)
- **Y-axis**: -100-0m (bias 0.6) + 0-100m (bias -0.6)
- **Z-axis**: Multiple layers with varying bias

### Event Management

- **preFracture**: Initialize fracture (SoloEvent at t=0)
- **pumpStart**: Limit dt during ramp-up (1 min to 1 min 5 s)
- **solverApplications**: Max dt = 30 s
- **outputs_vtk/silo**: Every 1 minute
- **restarts**: HaltEvent at 28 min wall-clock time

## Running the Simulation

### Step 1: Preprocess the XML Files

```bash
# Install geosx_xml_tools if not already available
pip install geosx_xml_tools

# Preprocess the benchmark file
preprocess_xml inputs/hydrofracture_benchmark.xml
```

This generates `inputs/hydrofracture_benchmark.xml.preprocessed` with all parameters and symbolic expressions evaluated.

### Step 2: Run GEOS

```bash
# Run the simulation
geosx -i inputs/hydrofracture_benchmark.xml.preprocessed

# Or with parallel execution
mpirun -np 8 geosx -i inputs/hydrofracture_benchmark.xml.preprocessed -x 2 -y 2 -z 2
```

### Step 3: Override Parameters at Runtime

```bash
# Example: Run with higher viscosity (5 cP instead of 1 cP)
geosx -i inputs/hydrofracture_benchmark.xml.preprocessed -p mu 0.005
```

## Visualizing Results

### Pre-simulation Visualization

```bash
python inputs/scripts/plot_hydrofracture_results.py
```

### Post-simulation Visualization

After running GEOS, load the output files in:

- **Paraview**: Open VTK files (may require Multi-block Inspector for fracture)
- **VisIt**: Open Silo files (recommended format)

## Geologic Model

The heterogeneous properties follow a 5-layer structure:

| Layer | Z (m) | σ_xx (MPa) | σ_yy (MPa) | σ_zz (MPa) | K (GPa) | G (GPa) |
|-------|-------|------------|------------|------------|---------|---------|
| 1 | -150 | 40 | 50 | 45 | 15 | 8 |
| 2 | -100 | 42 | 52 | 47 | 18 | 10 |
| 3 | 0 | 45 | 55 | 50 | 20 | 12 |
| 4 | 100 | 43 | 53 | 48 | 17 | 9 |
| 5 | 150 | 41 | 51 | 46 | 16 | 8.5 |

## Notes

- Units are SI throughout (Pa, m, s, kg)
- Injection source flux is in kg/s (not m³/s)
- The negative sign in source_scale indicates injection (mass added)
- Roller boundary conditions prevent rigid body motion
- The HaltEvent ensures graceful exit if wall-clock allocation is exceeded

## Troubleshooting

### XML Preprocessing Errors

Ensure geosx_xml_tools is installed:
```bash
pip install geosx_xml_tools
```

### Table File Not Found

Verify the `table_root` parameter points to the correct directory:
```xml
<Parameter name="table_root" value="./tables"/>
```

### Convergence Issues

Reduce timestep limits during pump ramp:
```xml
<Parameter name="pump_ramp_dt_limit" value="0.1 [s]"/>
```

## References

- GEOS Documentation: https://geosx-geosx.readthedocs-hosted.com/
- Based on: `inputFiles/hydraulicFracturing/heterogeneousInSitu_benchmark.xml`
