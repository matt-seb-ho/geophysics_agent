# Egg Model - Multiphase Flow with Wells Simulation

## Overview

This directory contains the GEOS input files for the Egg model, a benchmark case for multiphase flow simulation with wells. The model simulates water injection in a petroleum reservoir with:

- **4 Producer Wells** - Extracting oil and water
- **8 Injector Wells** - Injecting water for pressure maintenance and oil displacement
- **18,553 hexahedral cells** - Reservoir discretization
- **7 vertical layers** - All wells penetrate all layers

## Files

### Main Input Files

| File | Description |
|------|-------------|
| `deadOilEgg_base.xml` | Core physics setup: solvers, constitutive models, regions, field specs |
| `deadOilEgg_benchmark.xml` | Case-specific setup: mesh import and well definitions |
| `pvdo.txt` | Dead oil PVT table (pressure, formation volume factor, viscosity) |
| `pvtw.txt` | Water PVT table (reference pressure, formation volume factor, compressibility, viscosity) |

### Supporting Files

| File | Description |
|------|-------------|
| `scripts/plot_well_rates.py` | Python script to visualize well production rates |

## Requirements

### Mesh File

**IMPORTANT**: The simulation requires the `egg.vtu` mesh file, which is not included in this directory. 

You can obtain the Egg model mesh from:
- GEOS-Dev/GEOSDATA repository: `DataSets/Egg/egg.vtu`
- Original source: [Delft University Egg Model dataset](https://www.tno.nl/en/)

Place the `egg.vtu` file in the same directory as the input XML files (`inputs/`).

### PVT Data Files

The PVT tables are included:
- **pvdo.txt**: Oil phase properties (undersaturated dead oil)
  - Surface density: 848.9 kg/m³
  - Component molar weight: 114 g/mol
  
- **pvtw.txt**: Water phase properties
  - Surface density: 1025.2 kg/m³
  - Component molar weight: 18 g/mol
  - Reference pressure: 30.6 MPa
  - Compressibility: 1e-10 Pa⁻¹

## Running the Simulation

### Basic Run

```bash
cd inputs
geosx -i deadOilEgg_benchmark.xml
```

### Parallel Run (recommended for faster execution)

```bash
cd inputs
mpirun -np 4 geosx -i deadOilEgg_benchmark.xml
```

### Validation Only (check XML syntax without running)

```bash
cd inputs
geosx -i deadOilEgg_benchmark.xml -v
```

## Physics Configuration

### Solvers

1. **CompositionalMultiphaseReservoir** (`coupledFlowAndWells`)
   - Couples reservoir flow and well solvers
   - Nonlinear tolerance: 1.0e-4
   - Maximum Newton iterations: 10
   - Time step controls with adaptive stepping

2. **CompositionalMultiphaseFVM** (`compositionalMultiphaseFlow`)
   - TPFA finite volume discretization
   - Temperature: 297.15 K (24°C)

3. **CompositionalMultiphaseWell** (`compositionalMultiphaseWell`)
   - Handles well multiphase flow with control switching
   - Log level 1 provides control switch notifications

### Constitutive Models

- **Fluid**: DeadOilFluid (oil + water)
  - Phase names: {oil, water}
  - Surface densities: 848.9, 1025.2 kg/m³
  
- **Relative Permeability**: Brooks-Corey
  - Phase min volume fraction: 0.1 (oil), 0.2 (water)
  - Phase exponents: 4.0 (oil), 3.0 (water)
  
- **Rock**: CompressibleSolidConstantPermeability
  - Porosity: 0.2 (uniform)
  - Permeability: Imported from mesh PERM field

### Well Controls

**Producers** (4 wells):
- Control type: BHP (Bottom Hole Pressure)
- Target BHP: 39 MPa
- Reference elevation: 28 m

**Injectors** (8 wells):
- Control type: Total volume rate
- Target rate: 8e-3 m³/s (691.2 m³/day) per well
- Maximum BHP: 90 MPa
- Injection stream: 100% water ({0.0, 1.0})

### Initial Conditions

- **Pressure**: 40 MPa (uniform)
- **Composition**: 90% oil, 10% water
- **Temperature**: 297.15 K

### Simulation Duration

- **Maximum time**: 1.5e7 seconds (~173.6 days)
- **Initial time step**: 1e4 seconds
- **Maximum event dt**: 5e5 seconds

## Outputs

### VTK Output
- Visualization files for ParaView
- Output frequency: every 2e6 seconds (~23.1 days)

### Time History Output
- HDF5 files containing well production rates
- `wellRateHistory1.hdf5` through `wellRateHistory4.hdf5`
- One for each producer well

### Restart Output
- Checkpoint files for simulation restart
- Output frequency: every 7.5e6 seconds (~86.8 days)

## Post-Processing

### Visualize Well Rates

```bash
cd inputs
python scripts/plot_well_rates.py
```

This generates:
- `outputs/well_rates_plot.png` - Individual well rate plots
- `outputs/well_rates_combined.png` - Combined plot of all wells
- `outputs/well_rates_data.csv` - CSV export of rate data

### View in ParaView

```bash
paraview outputs/*.vtm  # or *.pvd file
```

## Simulation Summary

| Property | Value |
|----------|-------|
| Reservoir dimensions | ~480m × ~480m × 32m |
| Grid cells | 18,553 hexahedra |
| Active wells | 12 (4 producers + 8 injectors) |
| Total injection rate | 0.064 m³/s (5,529.6 m³/day) |
| Initial reservoir pressure | 40 MPa |
| Producer BHP | 39 MPa |
| Temperature | 24°C (297.15 K) |

## References

- Van Essen, G.M., et al. "Robust optimization of OPR in a thin-layered reservoir using the ensemble-based method." Computational Geosciences 17.5 (2013): 891-908.
- Jansen, J.D., et al. "The egg model - a geological ensemble for reservoir simulation." Geoscience Data Journal 1.2 (2014): 192-195.
