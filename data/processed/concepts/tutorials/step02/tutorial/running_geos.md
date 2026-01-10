**Context:** Tutorials > Step02 > Tutorial > Running GEOS

## Running GEOS
The command to run GEOS is

[`console
  path/to/geosx -i ../../../../../inputFiles/singlePhaseFlow/vtk/3D_10x10x10_compressible_tetra_gravity_smoke.xml

Again, all paths for files included in the XML file are relative
to this XML file, not to the GEOS executable.
When running GEOS, console messages will provide indications regarding the
status of the simulation.
In our case, the first lines are:

``console
  Adding Mesh: VTKMesh, CubeTetra
  Adding Event: PeriodicEvent, solverApplications
  Adding Event: PeriodicEvent, outputs
  Adding Event: PeriodicEvent, restarts
  Adding Solver of type SinglePhaseFVM, named SinglePhaseFlow
  Adding Geometric Object: Box, left
  Adding Output: Silo, siloOutput
  Adding Output: Restart, restartOutput
  Adding Object CellElementRegion named Domain from ObjectManager::Catalog.

Followed by:

``console
  VTKMesh 'CubeTetra': reading mesh from /path/to/inputFiles/singlePhaseFlow/vtk/cube_10x10x10_tet.vtk
  Generating global Ids from VTK mesh
  VTKMesh 'CubeTetra': generating GEOS mesh data structure
  Number of nodes:  366
    Number of elems: 1153
               C3D4: 1153
  Load balancing:  min  avg  max
  (element/rank): 1153 1153 1153
  regionQuadrature: meshBodyName, meshLevelName, regionName, subRegionName = CubeTetra, Level0, Domain, tetrahedra
  CubeTetra/Level0/Domain/tetrahedra/water allocated 1 quadrature points
  CubeTetra/Level0/Domain/tetrahedra/rock allocated 1 quadrature points

We see that we have now 366 nodes and 1153 tetrahedral elements.
And finally, when the simulation is successfully done we see:

``console
  Time: 0s, dt:1s, Cycle: 0
  Time: 1s, dt:1s, Cycle: 1
  Time: 2s, dt:1s, Cycle: 2
  Time: 3s, dt:1s, Cycle: 3
  Time: 4s, dt:1s, Cycle: 4
  Time: 5s, dt:1s, Cycle: 5
  ...
  Time: 95s, dt:1s, Cycle: 95
  Time: 96s, dt:1s, Cycle: 96
  Time: 97s, dt:1s, Cycle: 97
  Time: 98s, dt:1s, Cycle: 98
  Time: 99s, dt:1s, Cycle: 99
  Cleaning up events
  SinglePhaseFlow, number of time steps: 100
  SinglePhaseFlow, number of successful nonlinear iterations: 100
  SinglePhaseFlow, number of successful linear iterations: 1000
  SinglePhaseFlow, number of time step cuts: 0
  SinglePhaseFlow, number of discarded nonlinear iterations: 0
  SinglePhaseFlow, number of discarded linear iterations: 0
  Umpire            HOST sum across ranks:    1.9 MB
  Umpire            HOST         rank max:    1.9 MB
  total time                         5.837s
  initialization time                0.094s
  run time                           5.432s

  Process finished with exit code 0

