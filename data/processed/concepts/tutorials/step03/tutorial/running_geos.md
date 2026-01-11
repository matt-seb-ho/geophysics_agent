**Context:** Tutorials > Step03 > Tutorial > Running GEOS

## Running GEOS
The simulation can be launched with:

``console
  geosx -i FieldCaseTutorial3_smoke.xml

One can notice the correct load of the field function among the starting output messages

``console
        Adding Mesh: VTKMesh, SyntheticMesh
        Adding Event: PeriodicEvent, solverApplications
        Adding Event: PeriodicEvent, outputs
        Adding Solver of type SinglePhaseFVM, named SinglePhaseFlow
        Adding Geometric Object: Box, all
        Adding Geometric Object: Box, source
        Adding Geometric Object: Box, sink
        Adding Output: VTK, reservoir_with_properties
           TableFunction: timeInj
           TableFunction: initialPressureFunc
           TableFunction: permxFunc
           TableFunction: permyFunc
           TableFunction: permzFunc
        Adding Object CellElementRegion named Reservoir from ObjectManager::Catalog.
        Adding Object CellElementRegion named Burden from ObjectManager::Catalog.

------------------------------------