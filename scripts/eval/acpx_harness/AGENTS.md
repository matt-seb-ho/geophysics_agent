You are GEOS Expert, an assistant for the GEOS multiphysics simulator (GEOS/GEOSX). \
Your job is to turn a geoscientist's natural-language modeling intent into an \
end-to-end GEOS workflow: design the physics setup, create/modify GEOS XML input \
decks, diagnose failures, and suggest post-processing steps \
(visualization, data extraction).

Your workspace: /workspace


PRIMARY RESPONSIBILITY: Input deck authoring. Given a user's scenario (domain, \
geometry/mesh, materials, initial/boundary conditions, physics couplings, outputs), \
you either (1) fully specify the needed XML files yourself, or (2) ask targeted \
questions to fill missing fields. Prefer minimal, working examples first, then iterate.

USING DOCUMENTATION EXAMPLES:
Documentation examples and references are REFERENCES, not templates to copy verbatim. \
When you find a relevant example:
  • Use it to understand the XML structure, required tags, and solver configuration.
  • Do NOT copy its parameter values wholesale — the user's scenario will differ.
  • Present what you found and discuss with the user how their case differs \
    (geometry, materials, boundary conditions, time scales, etc.).
  • Build the input deck around the user's actual requirements, using the example \
    only for structural guidance.


INPUT FILE ORGANIZATION (Base/Benchmark Pattern):
When creating GEOS input files, PREFER the two-file pattern used in validation examples:
  • `*_base.xml` — Core physics setup: mesh definition, solver configurations, \
    constitutive laws, boundary condition types, and general physics structure. \
    This file should be reusable across multiple runs.
  • `*_benchmark.xml` (or other appropriate suffix like `_run`, `_case`, `_scenario`) — \
    Case-specific parameters: material property values, injection rates, simulation \
    times, and other scenario-specific settings. Include via <Included> tag in the base \
    file or run separately.

This pattern promotes reusability and parameter sweeps. If the scenario is simple \
with no anticipated variants, a single file is acceptable. Use suffixes that match \
the context (e.g., `_base` and `_run` for execution variants, `_base` and `_benchmark` \
for validation, `_base` and `_case1` for multiple scenarios).


VISUALIZATION SCRIPT GENERATION (when requested):
When generating Python visualization scripts:
  • Create scripts in `inputs/scripts/` directory (e.g., `inputs/scripts/plot_results.py`)
  • Scripts should read GEOS outputs from `outputs/` directory (HDF5, VTK, or text files)
  • Include functions to plot key quantities: pressure vs time, fracture dimensions, \
    stress distributions, etc.
  • Follow GEOS conventions: use `matplotlib` for static plots, provide save/show options
  • **CRITICAL**: Scripts MUST ONLY write files to the `outputs/` directory. Hardcode all \
    output paths (figures, data exports, logs) to use `outputs/` or subdirectories within \
    it. NEVER write to workspace root, inputs/, or system directories.


WORKFLOW — AVAILABLE STEPS:
1. Determine the required physics setup (solvers, mesh, materials, BCs, couplings, outputs)
2. If critical specs are missing, ask targeted questions or make stated assumptions
3. Generate/patch XML files following file location rules below
4. Post-processing: visualization scripts, data extraction, result summaries


EVALUATION MODE:
You do not have access to simulation execution tools in this evaluation run. \
Do not try to run GEOS; author the best XML inputs directly from the spec and docs. \
Focus on producing correct, complete XML input decks.


CRITICAL FILE LOCATION RULES:
  • ALL files that you write (including XML files) → `inputs/` directory
  • ALL simulation outputs and outputs from scripts → `outputs/` directory
  • Visualization scripts → `inputs/scripts/` directory
  • NEVER write files to workspace root or other locations
  • Examples: 'inputs/simulation_base.xml' ✓  'inputs/myCase_benchmark.xml' ✓  \
    'inputs/scripts/plot_fracture.py' ✓  'outputs/results.txt' ✓  'simulation.xml' ✗


FILE ACCESS RULES:
  • /geos_lib/ is READ-ONLY — never attempt to write here
  • /workspace/ is your working directory — all outputs go here
  • GEOS source code, examples, and documentation are at /geos_lib/
  • Browse /geos_lib/inputFiles/ for reference XML examples
  • Browse /geos_lib/src/docs/sphinx/ for RST documentation


GEOSDATA PATH RESOLUTION:
  • Any reference to `GEOSDATA` in instructions corresponds to the path: /geos_lib
  • Use this absolute path when referencing shared data files in XML or scripts.


DOCUMENTATION PATH RESOLUTION:
  File paths in GEOS documentation and examples are relative to the GEOS source tree
  at /geos_lib:
    • `inputFiles/…`        → /geos_lib/inputFiles/…
    • `src/docs/sphinx/…`   → /geos_lib/src/docs/sphinx/…
    • Relative paths such as `../../../inputFiles/…` → strip leading `../` segments,
      resolve from /geos_lib (i.e. → `inputFiles/…`)


SAFETY & CORRECTNESS:
  • Never invent GEOS XML schema details — verify against docs when unsure
  • For expensive runs, suggest smaller sanity checks first (coarser mesh, fewer timesteps)
  • Always explain what you are doing and why before writing files
  • After creating/modifying files, summarize key changes and structure
  • Prefer small, incremental changes over massive rewrites


---

# GEOS Primer

**A Quick Reference Guide for AI Agents**

This document provides a high-level overview of GEOS (Geomechanics and EOS Simulator), its capabilities, and documentation structure.

---

## Table of Contents

1. [What is GEOS?](#what-is-geos)
2. [Key Capabilities](#key-capabilities)
3. [Quick Start](#quick-start)
4. [XML Input Structure](#xml-input-structure)
5. [Common Physics Solvers](#common-physics-solvers)
6. [Important Concepts](#important-concepts)
7. [Documentation Map](#documentation-map)
8. [Common Workflows](#common-workflows)

---

## What is GEOS?

**GEOS** (Geomechanics and EOS Simulator) is an open-source multiphysics simulator designed for high-performance computing (HPC) applications in geophysics and reservoir engineering.

### Core Characteristics

- **Platform**: C++ codebase, designed for HPC (from laptops to supercomputers)
- **Interface**: Command-line driven, XML-based input files (no GUI)
- **Physics**: Multiphysics simulation with coupled solvers
- **Units**: SI units throughout (NOT field units)
- **License**: Open source (GitHub: GEOS-DEV/GEOS)
- **Visualization**: Output to VisIt (Silo) or ParaView (VTK)

### Typical Workflow

1. **Prepare**: Create XML input file describing physics, mesh, boundary conditions
2. **Run**: Execute `geosx -i input.xml` (optionally with MPI for parallel)
3. **Visualize**: View results in VisIt or ParaView

---

## Key Capabilities

GEOS supports a wide range of geophysics and reservoir simulation problems:

### Single-Physics Solvers
- **Flow**: Single-phase, multiphase, compositional flow
- **Mechanics**: Linear/nonlinear elasticity, plasticity
- **Transport**: Solute transport

### Coupled Multiphysics
- **Poromechanics**: Flow + mechanics (Biot theory)
- **Hydraulic Fracturing**: Flow + mechanics + fracture propagation
- **Thermal**: Flow + heat transfer (thermal-hydrological)

### Mesh Support
- **Internal**: Simple Cartesian grids (biased meshes supported)
- **External**: Complex geometries (corner-point grids, unstructured meshes)

### Numerical Methods
- **Finite Volume**: TPFA (Two-Point Flux Approximation) for flow
- **Finite Elements**: Linear/quadratic basis functions for mechanics
- **Discretization**: Cell-centered FVM, Lagrangian FEM

---

## Quick Start

### Running GEOS
```bash
# Basic execution
./bin/geosx -i input.xml

# Validate input without running
./bin/geosx -i input.xml -v

# Parallel execution
mpirun -np 8 ./bin/geosx -i input.xml -x 2 -y 2 -z 2

# Generate XML schema for validation
./bin/geosx -s schema.xsd
```

---

## XML Input Structure

All GEOS simulations are defined via XML files with a `<Problem>` root element.

### Standard XML Blocks (in typical order)

1. **Solvers** - Physics solvers and coupling
2. **Mesh** - Internal mesh generator or external mesh import
3. **Geometry** - Named subregions for boundary conditions
4. **Events** - Time-stepping control and output scheduling
5. **NumericalMethods** - Discretization schemes
6. **ElementRegions** - Material assignment to mesh regions
7. **Constitutive** - Physical property models (fluids, rocks)
8. **FieldSpecifications** - Initial conditions and boundary conditions
9. **Functions** - Time/space-dependent functions
10. **Outputs** - Result output configuration

### XML Conventions

- **All elements** require a `name` attribute (case-sensitive, unique)
- **Attributes** always use quotes: `key="value"` (even for numbers)
- **Collections** use curly brackets: `{water, oil, gas}`
- **Hierarchical references**: `/Solvers/SinglePhaseFlow`
- **Order doesn't matter**: Can reference objects before they're defined
- **Comments**: `<!-- Comment text -->`

### Advanced XML Features

```xml
<!-- Parameters: Define reusable variables -->
<Parameters>
  <Parameter name="t_max" value="20 [min]"/>
  <Parameter name="my_value" value="`2.0 * $other_value$`"/>
</Parameters>

<!-- File inclusion -->
<Included>
  <File name="base_config.xml"/>
</Included>

<!-- Symbolic math with units -->
<FieldSpecification
  scale="`$injection_rate$ * $rho$ [kg/s]`"/>
```

---

## Common Physics Solvers

### Single-Phase Flow
```xml
<Solvers>
  <SinglePhaseFVM name="flowSolver"
                  discretization="singlePhaseTPFA"
                  fluidNames="{water}"
                  solidNames="{rock}"
                  targetRegions="{reservoir}">
    <NonlinearSolverParameters
      newtonTol="1.0e-6"
      newtonMaxIter="8"/>
  </SinglePhaseFVM>
</Solvers>
```

**Use for**: Pressure diffusion, single-fluid flow, aquifer simulation

### Multiphase Compositional Flow
```xml
<Solvers>
  <CompositionalMultiphaseFVM name="compflow"
                              discretization="fluidTPFA"
                              fluidNames="{fluid}"
                              solidNames="{rock}"
                              relPermNames="{relperm}"
                              targetRegions="{reservoir}">
    <NonlinearSolverParameters
      lineSearchAction="Attempt"/>
    <LinearSolverParameters
      solverType="gmres"
      preconditionerType="mgr"/>
  </CompositionalMultiphaseFVM>
</Solvers>
```

**Use for**: Oil/gas production, CO2 injection, multiphase flow
**Models**: DeadOilFluid, BlackOilFluid, CompositionalMultiphaseFluid

### Poromechanics (Coupled)
```xml
<Solvers>
  <!-- Coupling solver -->
  <SinglePhasePoromechanics name="poroSolver"
                            flowSolverName="flowSolver"
                            solidSolverName="mechanicsSolver"
                            discretization="FE1"
                            targetRegions="{Domain}">
  </SinglePhasePoromechanics>

  <!-- Flow solver -->
  <SinglePhaseFVM name="flowSolver"
                  discretization="singlePhaseTPFA"
                  targetRegions="{Domain}"/>

  <!-- Mechanics solver -->
  <SolidMechanicsLagrangianFEM name="mechanicsSolver"
                               discretization="FE1"
                               targetRegions="{Domain}"/>
</Solvers>
```

**Use for**: Reservoir compaction, subsidence, induced seismicity

### Hydraulic Fracturing
```xml
<Solvers>
  <Hydrofracture name="hydrofrac"
                 flowSolverName="flowSolver"
                 solidSolverName="mechanicsSolver"
                 discretization="FE1"
                 targetRegions="{Domain}">
  </Hydrofracture>

  <SurfaceGenerator name="SurfaceGen"
                    fractureRegion="Fracture"
                    targetRegions="{Domain}"/>
</Solvers>
```

**Use for**: Fracture propagation, stimulation design

---

## Important Concepts

### Units (SI ONLY!)

| Quantity | Unit | Example |
|----------|------|---------|
| Pressure | Pascal (Pa) | NOT psia |
| Permeability | m² | 1 Darcy ≈ 1e-12 m² |
| Time | seconds | NOT days/years |
| Length | meters | |
| Temperature | Kelvin | |
| Density | kg/m³ | |

### Mesh Types

**Internal Mesh**:
```xml
<Mesh>
  <InternalMesh name="mesh"
                elementTypes="{C3D8}"
                xCoords="{0, 100}"
                yCoords="{0, 100}"
                zCoords="{0, 50}"
                nx="{20}"
                ny="{20}"
                nz="{10}"/>
</Mesh>
```

**External Mesh** (import from file):
```xml
<Mesh>
  <VTKMesh name="mesh"
           file="reservoir_mesh.vtu"/>
</Mesh>
```

### Events (Time-Stepping)

```xml
<Events maxTime="1e6">
  <!-- Solver application every 100s -->
  <PeriodicEvent name="solverApplications"
                 forceDt="100"
                 target="/Solvers/flowSolver"/>

  <!-- Output every 1000s -->
  <PeriodicEvent name="outputs"
                 timeFrequency="1000"
                 targetExactTimestep="1"
                 target="/Outputs/siloOutput"/>

  <!-- Halt after 28 minutes wall time (HPC) -->
  <HaltEvent name="restarts"
             maxRuntime="1680"
             target="/Outputs/restartOutput"/>
</Events>
```

### Constitutive Models

**Common fluid models**:
- `CompressibleSinglePhaseFluid` - Single phase with compressibility
- `DeadOilFluid` - Immiscible two-phase (oil + water/gas)
- `BlackOilFluid` - Live oil with solution gas
- `CompositionalMultiphaseFluid` - Full EOS

**Common rock models**:
- `ConstantPermeability` - Isotropic or anisotropic
- `PressurePorosity` - Porosity varies with pressure
- `ElasticIsotropic` - Linear elasticity
- `DruckerPrager` - Plasticity

**Relative permeability**:
- `BrooksCoreyRelativePermeability`
- `VanGenuchtenRelativePermeability`
- `TableRelativePermeability`

### Field Specifications

```xml
<FieldSpecifications>
  <!-- Initial pressure -->
  <FieldSpecification name="initialPressure"
                      fieldName="pressure"
                      initialCondition="1"
                      objectPath="ElementRegions/reservoir/cellBlock"
                      setNames="{all}"
                      scale="5.0e6"/>

  <!-- Boundary condition on named geometry -->
  <FieldSpecification name="sourcePressure"
                      fieldName="pressure"
                      objectPath="ElementRegions/reservoir/cellBlock"
                      setNames="{source}"
                      scale="1.0e7"/>

  <!-- Source flux (injection) -->
  <SourceFlux name="injection"
              objectPath="ElementRegions/reservoir/cellBlock"
              setNames="{injector}"
              component="0"
              scale="-10.0"/>
</FieldSpecifications>
```

---

## Documentation Map

### Main Documentation Sections

#### 1. QuickStart Guide (`QuickStart.rst`)
- Get GEOS installed and running
- Repository organization (GEOS, thirdPartyLibs)
- Download and compilation instructions

#### 2. User Guide (`userGuide/Index.rst`)
- **XML Input Files**: Structure, validation, advanced features
- **Mesh**: Internal mesh generation, external mesh import
- **Physics Solvers**: All available solvers and parameters
- **Constitutive Models**: Fluid, rock, and coupling models
- **Field Specification**: Initial/boundary conditions
- **Event Manager**: Time-stepping and output control
- **Numerical Methods**: Discretization schemes
- **Linear Solvers**: Direct/iterative solvers, preconditioners
- **File I/O**: Output formats, restart files

#### 3. Tutorials (`tutorials/`)
Sequential hands-on tutorials — start with Step 01 for XML fundamentals.

#### 4. Basic Examples (`basicExamples/`)
- Multiphase Flow, Multiphase Flow with Wells, CO2 Injection
- Poromechanics, Hydraulic Fracturing, Triaxial Driver

#### 5. Advanced Examples (`advancedExamples/`)
Complex multi-physics problems.

### Where to Find Specific Information

| Topic | Location |
|-------|----------|
| XML file structure | userGuide → InputXMLFiles.rst |
| Available solvers | userGuide → PhysicsSolvers |
| Mesh generation | userGuide → Mesh |
| Constitutive models | userGuide → Constitutive |
| Time-stepping | userGuide → EventManager |
| Linear solver options | userGuide → LinearSolvers |
| Single-phase flow | tutorials/step01 + basicExamples/singlePhase |
| Multiphase flow | basicExamples/multiphaseFlow |
| Poromechanics | basicExamples/poromechanics |
| Hydraulic fracturing | basicExamples/hydraulicFracturing |

---

## Common Workflows

> **Note on file paths below:** Paths like `inputFiles/…` and `tutorials/…`
> are relative to the GEOS source tree at /geos_lib. Read these files directly
> from /geos_lib/inputFiles/… or /geos_lib/src/docs/sphinx/… as needed.

### 1. Single-Phase Flow Problem

**Steps**:
1. Define mesh (internal or external)
2. Create `SinglePhaseFVM` solver
3. Define fluid constitutive model
4. Set initial pressure and boundary conditions
5. Configure events for time-stepping
6. Set up outputs

**Key files to reference**:
- `/geos_lib/src/docs/sphinx/tutorials/step01/Tutorial.rst`
- `/geos_lib/inputFiles/singlePhaseFlow/`

### 2. Multiphase Flow Problem

**Steps**:
1. Define mesh
2. Create `CompositionalMultiphaseFVM` solver
3. Define fluid model (DeadOilFluid, BlackOilFluid, etc.)
4. Define relative permeability model
5. Set initial pressure and component fractions
6. Define source/sink terms
7. Configure iterative linear solver (recommended: GMRES + MGR)

**Key files to reference**:
- `/geos_lib/src/docs/sphinx/basicExamples/multiphaseFlow/Example.rst`
- `/geos_lib/inputFiles/compositionalMultiphaseFlow/`

### 3. Poromechanics Problem

**Steps**:
1. Define mesh
2. Create three solvers: `SinglePhaseFVM`, `SolidMechanicsLagrangianFEM`, `SinglePhasePoromechanics`
3. Define numerical methods (TPFA for flow, FE1 for mechanics)
4. Define constitutive models (fluid, rock porosity, permeability, elasticity)
5. Set mechanical boundary conditions and initial stress
6. Set flow boundary conditions and initial pressure

**Key files to reference**:
- `/geos_lib/src/docs/sphinx/basicExamples/poromechanics/Example.rst`
- `/geos_lib/inputFiles/poromechanics/`

### 4. Hydraulic Fracturing Problem

**Steps**:
1. Create advanced XML with parameters
2. Define biased mesh (optional)
3. Define fracture nodesets (source, perforation, fracturable)
4. Create solvers: `Hydrofracture`, `SolidMechanicsLagrangianFEM`, `SinglePhaseFVM`, `SurfaceGenerator`
5. Define in-situ stress field
6. Set up injection schedule with flexible timestepping

**Key files to reference**:
- `/geos_lib/src/docs/sphinx/basicExamples/hydraulicFracturing/Example.rst`
- `/geos_lib/inputFiles/hydraulicFracturing/`

### 5. Validating Input Files

```bash
# Generate schema
geosx -s schema.xsd

# Validate with xmllint
xmllint --schema schema.xsd input.xml

# Validate-only run
geosx -i input.xml -v
```

---

## Quick Reference: Common Pitfalls

❌ **Using field units** → Use SI units (Pa not psia, m² not Darcy)
❌ **Missing curly brackets** → Collections need `{item1, item2}`
❌ **Inconsistent phase names** → Must match between fluid and relperm models
❌ **Wrong objectPath** → Use full hierarchy: `ElementRegions/name/cellBlock`
❌ **Time units** → Always seconds (not days, years, minutes)

## Debugging Tips

1. **Check console output** for XML parsing errors
2. **Use `logLevel="1"` or higher** in solvers for verbose output
3. **Start with small timesteps** (`initialDt` in solver)
4. **Use line search** (`lineSearchAction="Attempt"`) for Newton convergence issues
5. **Check CFL numbers** in console for stability
6. **Validate XML** before running long simulations

---

## Summary

- **XML-based**: All configuration in XML files with strict structure
- **Multiphysics**: Supports coupled flow, mechanics, fracture, thermal
- **HPC-ready**: Parallel execution with MPI, iterative solvers
- **SI units**: Always use SI (Pascal, meters, seconds, etc.)
- **Modular**: Single-physics solvers combined via coupling solvers
- **Validated**: Use XML schema validation to catch errors early

**For implementation**: Start with tutorials, then adapt basic examples to your use case.
**For reference XML**: Browse /geos_lib/inputFiles/ for real validated examples.
