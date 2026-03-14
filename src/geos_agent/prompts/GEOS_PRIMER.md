# GEOS Primer

**A Quick Reference Guide for AI Agents**

This document provides a high-level overview of GEOS (Geomechanics and EOS Simulator), its capabilities, and documentation structure to help ground searches in the RAG system.

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
9. [RAG Tools Reference](#rag-tools-reference)

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

### Installation
```bash
# Clone repositories
git clone https://github.com/GEOS-DEV/GEOS.git
git clone https://github.com/GEOS-DEV/thirdPartyLibs.git

# Build TPLs (third-party libraries)
cd thirdPartyLibs
python scripts/config-build.py -hc ../GEOS/host-configs/your-platform.cmake -bt Release
cd build-your-platform-release
make

# Build GEOS
cd ../../GEOS
python scripts/config-build.py -hc host-configs/your-platform.cmake -bt Release
cd build-your-platform-release
make -j4
make install
```

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

This section provides a roadmap to the GEOS documentation structure.

### Main Documentation Sections

#### 1. QuickStart Guide (`QuickStart.rst`)
- **Purpose**: Get GEOS installed and running
- **Topics**:
  - FAQ for new users
  - Repository organization (GEOS, thirdPartyLibs)
  - Download and compilation instructions
  - Host-config files for different platforms
  - Testing the installation

#### 2. User Guide (`userGuide/Index.rst`)
Comprehensive documentation on all GEOS components:

- **XML Input Files**: Structure, validation, advanced features
- **Mesh**: Internal mesh generation, external mesh import
- **Physics Solvers**: All available solvers and parameters
- **Constitutive Models**: Fluid, rock, and coupling models
- **Field Specification**: Initial/boundary conditions
- **Event Manager**: Time-stepping and output control
- **Numerical Methods**: Discretization schemes
- **Linear Solvers**: Direct/iterative solvers, preconditioners
- **File I/O**: Output formats, restart files
- **pygeosx**: Python interface for scripting

#### 3. Tutorials (`tutorials/`)
Sequential hands-on tutorials (start with Step 01):

- **Step 01**: First Steps - Single-phase flow basics
  - XML structure fundamentals
  - Internal mesh generation
  - Running and visualizing results

- **Step 02-04**: (Build on Step 01 concepts)

#### 4. Basic Examples (`basicExamples/`)
Application-focused examples demonstrating workflows:

- **Multiphase Flow**: SPE10 dead oil example
  - `CompositionalMultiphaseFVM` solver
  - Relative permeability models
  - Source/sink boundary conditions

- **Multiphase Flow with Wells**: Well modeling

- **CO2 Injection**: Carbon sequestration

- **Poromechanics**: Terzaghi consolidation
  - Coupled flow + mechanics
  - `SinglePhasePoromechanics` solver
  - Finite volume + finite elements

- **Hydraulic Fracturing**: Fracture propagation
  - `Hydrofracture` solver
  - Advanced XML features (parameters, symbolic math)
  - Surface generation and fracture growth

- **Triaxial Driver**: Rock mechanics testing

#### 5. Advanced Examples (`advancedExamples/`)
More complex multi-physics problems

#### 6. Build Guide (`buildGuide/`)
Advanced compilation topics:
- Platform-specific configurations
- GPU acceleration
- Custom compiler options

#### 7. Developer Guide (`developerGuide/`)
For code contributors:
- Code structure
- Adding new physics
- Testing framework

### Where to Find Specific Information

| Topic | Location |
|-------|----------|
| How to run GEOS | QuickStart.rst |
| XML file structure | userGuide → InputXMLFiles.rst |
| Available solvers | userGuide → PhysicsSolvers |
| Mesh generation | userGuide → Mesh |
| Constitutive models | userGuide → Constitutive |
| Time-stepping | userGuide → EventManager |
| Linear solver options | userGuide → LinearSolvers |
| Output formats | userGuide → File I/O |
| Single-phase flow | tutorials/step01 + basicExamples/singlePhase |
| Multiphase flow | basicExamples/multiphaseFlow |
| Poromechanics | basicExamples/poromechanics |
| Hydraulic fracturing | basicExamples/hydraulicFracturing |
| Advanced XML (parameters, units) | basicExamples/hydraulicFracturing |

---

## Common Workflows

> **Note on file paths below:** Paths like `inputFiles/…` and `tutorials/…`
> are relative to the GEOS source tree (`GEOS_SOURCE_DIR`). Use the
> `read_file` tool to retrieve their contents — it resolves the path
> automatically.

### 1. Single-Phase Flow Problem

**Steps**:
1. Define mesh (internal or external)
2. Create `SinglePhaseFVM` solver
3. Define fluid constitutive model
4. Set initial pressure and boundary conditions
5. Configure events for time-stepping
6. Set up outputs

**Key files to reference**:
- `tutorials/step01/Tutorial.rst`
- `inputFiles/singlePhaseFlow/`

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
- `basicExamples/multiphaseFlow/Example.rst`
- `inputFiles/compositionalMultiphaseFlow/`

### 3. Poromechanics Problem

**Steps**:
1. Define mesh
2. Create three solvers:
   - `SinglePhaseFVM` for flow
   - `SolidMechanicsLagrangianFEM` for mechanics
   - `SinglePhasePoromechanics` coupling solver
3. Define numerical methods (TPFA for flow, FE1 for mechanics)
4. Define constitutive models (fluid, rock porosity, permeability, elasticity)
5. Set mechanical boundary conditions and initial stress
6. Set flow boundary conditions and initial pressure

**Key files to reference**:
- `basicExamples/poromechanics/Example.rst`
- `inputFiles/poromechanics/`

### 4. Hydraulic Fracturing Problem

**Steps**:
1. Create advanced XML with parameters
2. Define biased mesh (optional)
3. Define fracture nodesets (source, perforation, fracturable)
4. Create solvers:
   - `Hydrofracture` coupling solver
   - `SolidMechanicsLagrangianFEM` for mechanics
   - `SinglePhaseFVM` for flow
   - `SurfaceGenerator` for fracture propagation
5. Define in-situ stress field
6. Set up injection schedule with flexible timestepping

**Key files to reference**:
- `basicExamples/hydraulicFracturing/Example.rst`
- `inputFiles/hydraulicFracturing/`

### 5. Validating Input Files

**Before running**:
```bash
# Generate schema
geosx -s schema.xsd

# Validate with xmllint
xmllint --schema schema.xsd input.xml

# Validate-only run
geosx -i input.xml -v
```

**In text editor**:
- Use XML validation plugins (Sublime: Exalt, VSCode: RedHat XML)
- Point to schema.xsd for real-time validation

---

## Quick Reference: Common Tasks

### Finding Information in RAG

When searching the GEOS knowledge base, three collections are available — use the right one for the right question:

1. **Conceptual questions** → `search_navigator` (Navigator collection):
   - "What is poromechanics?"
   - "How does GEOS handle multiphase flow?"
   - "Which tutorial covers hydraulic fracturing?"
   - Returns: document/section titles, breadcrumbs, source `.rst` path
   - Follow-up: optionally call `read_file` on the returned `source` path to read the raw RST

2. **Syntax / attribute lookup** → `search_schema` (Schema collection) — **try this first for any element-level question**:
   - "What attributes does ViscoDruckerPrager take?"
   - "Is targetRegions required for solvers?"
   - "What is the default value of cflFactor?"
   - "What parameters does InternalMesh accept?"
   - Returns: the **complete attribute spec inline** (name, type, default, description for every attribute) — no `read_file` call needed
   - Source: authoritative GEOS XML schema (`geos_schema.xsd`), exhaustive across all 250 element types

3. **Real-world usage examples** → `search_technical` (Technical collection):
   - "Show me a working ViscoDruckerPrager constitutive block"
   - "Example XML for a TriaxialDriver setup"
   - "How is SinglePhasePoromechanics typically structured?"
   - Returns: `xml_reference` path + `line_range` markers pointing to a real example file
   - Follow-up: call `read_file(xml_reference, start_marker=..., end_marker=...)` to retrieve the snippet

4. **Recommended call order for writing a new XML block**:
   1. `search_schema("<ElementName>")` → get all valid attributes and their defaults
   2. `search_technical("<ElementName> example")` → get a real usage example for context
   3. `read_file(xml_reference, ...)` → retrieve the actual XML snippet to adapt

### Common Pitfalls

❌ **Using field units** → Use SI units (Pa not psia, m² not Darcy)
❌ **Missing curly brackets** → Collections need `{item1, item2}`
❌ **Inconsistent phase names** → Must match between fluid and relperm models
❌ **Wrong objectPath** → Use full hierarchy: `ElementRegions/name/cellBlock`
❌ **Time units** → Always seconds (not days, years, minutes)

### Debugging Tips

1. **Check console output** for XML parsing errors
2. **Use `logLevel="1"` or higher** in solvers for verbose output
3. **Start with small timesteps** (`initialDt` in solver)
4. **Use line search** (`lineSearchAction="Attempt"`) for Newton convergence issues
5. **Check CFL numbers** in console for stability
6. **Validate XML** before running long simulations

---

## Summary

GEOS is a powerful multiphysics simulator for geophysics applications. Key points:

- **XML-based**: All configuration in XML files with strict structure
- **Multiphysics**: Supports coupled flow, mechanics, fracture, thermal
- **HPC-ready**: Parallel execution with MPI, iterative solvers
- **SI units**: Always use SI (Pascal, meters, seconds, etc.)
- **Modular**: Single-physics solvers combined via coupling solvers
- **Validated**: Use XML schema validation to catch errors early

**For implementation**: Start with tutorials, then adapt basic examples to your use case.

**For questions**: Use `search_navigator` for conceptual/doc orientation, `search_schema` for authoritative attribute specs (no follow-up needed), `search_technical` for real usage examples, then `read_file` to retrieve the actual XML snippet.

---

## RAG Tools Reference

Three ChromaDB collections are available, each serving a distinct purpose.

### `search_navigator` — Conceptual navigation
- **Source**: All `.rst` documentation files (user guide, tutorials, examples)
- **Chunks**: One per RST document + one per section heading (~571 total)
- **Embedding**: RST prose (title + intro/section text)
- **Returns**: `title`, `breadcrumbs`, `source` (`.rst` path), `type` (document/section), text preview
- **When to use**: Orient yourself — find *which* doc or section covers a topic
- **Follow-up**: `read_file(source_path)` to read the raw RST if needed

### `search_schema` — Authoritative attribute specs
- **Source**: `data/geos_schema.xsd` — the GEOS XML schema generated directly from the C++ codebase
- **Chunks**: One per XML element type (250 total, exhaustive)
- **Embedding**: Element name + all attribute names, types, defaults, and descriptions
- **Returns**: `element`, `attribute_count`, `spec` (full inline listing — no follow-up needed)
- **When to use**: Any time you need to know what attributes an element accepts, their types, defaults, or what they mean
- **Key advantage**: Exhaustive — covers all 250 element types including those with no tutorial example; answer is in the chunk itself

### `search_technical` — Real usage examples
- **Source**: `Example.rst` files that contain `literalinclude` directives pointing to XML files
- **Chunks**: One per `literalinclude` reference (~334 total)
- **Embedding**: RST context prose + XML tag names + key attribute values from the referenced XML
- **Returns**: `xml_reference` (path to XML file), `line_range` (marker pair or line numbers), `breadcrumbs`, shadow text preview
- **When to use**: See how an element is actually used in a validated simulation
- **Follow-up**: Always call `read_file(xml_reference, start_marker=..., end_marker=...)` to retrieve the actual XML

### Decision guide

| Question type | Tool | Follow-up |
|---|---|---|
| "Where is X documented?" | `search_navigator` | Optional `read_file` on `.rst` |
| "What attributes does X take?" | `search_schema` | None — answer is inline |
| "What's the default for attribute Y on element X?" | `search_schema` | None |
| "Show me a working X block" | `search_technical` | `read_file(xml_reference, ...)` |
| "How is X typically structured in practice?" | `search_technical` | `read_file(xml_reference, ...)` |
| "What solver handles poromechanics?" | `search_navigator` | Optional |

---

*This primer is based on GEOS documentation as of the latest version. For the most up-to-date information, consult the official documentation at https://geosx-geosx.readthedocs-hosted.com/*
