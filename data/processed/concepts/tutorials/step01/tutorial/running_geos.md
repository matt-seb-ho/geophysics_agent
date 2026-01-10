**Context:** Tutorials > Step01 > Tutorial > Running GEOS

## Running GEOS
The command to run GEOS is

[path/to/geosx -i path/to/this/xml_file.xml`

Note that all paths for files included in the XML file are relative to this XML file.

While running GEOS, it logs status information on the console output with a verbosity
that is controlled at the object level, and
that can be changed using the `logLevel` flag.

The first few lines appearing to the console are indicating that the XML elements are read and registered correctly:

``sh
  Adding Solver of type SinglePhaseFVM, named SinglePhaseFlow
  Adding Mesh: InternalMesh, mesh
  Adding Geometric Object: Box, source
  Adding Geometric Object: Box, sink
  Adding Event: PeriodicEvent, solverApplications
  Adding Event: PeriodicEvent, outputs
  Adding Output: Silo, siloOutput
  Adding Object CellElementRegion named mainRegion from ObjectManager::Catalog.
    mainRegion/cellBlock/water is allocated with 1 quadrature points.
    mainRegion/cellBlock/rock is allocated with 1 quadrature points.
    mainRegion/cellBlock/rockPerm is allocated with 1 quadrature points.
    mainRegion/cellBlock/rockPorosity is allocated with 1 quadrature points.
    mainRegion/cellBlock/nullSolid is allocated with 1 quadrature points.


Then, we go into the execution of the simulation itself:

``sh
  Time: 0s, dt:20s, Cycle: 0
      Attempt:  0, NewtonIter:  0
      ( R ) = ( 5.65e+00 ) ;
      Attempt:  0, NewtonIter:  1
      ( R ) = ( 2.07e-04 ) ;
      Last LinSolve(iter,res) = (  63, 8.96e-11 ) ;
      Attempt:  0, NewtonIter:  2
      ( R ) = ( 9.86e-11 ) ;
      Last LinSolve(iter,res) = (  70, 4.07e-11 ) ;


Each time iteration at every 20s interval is logged to console, until the end of the simulation at `maxTime=5000`:

``sh
  Time: 4980s, dt:20s, Cycle: 249
      Attempt:  0, NewtonIter:  0
      ( R ) = ( 4.74e-09 ) ;
      Attempt:  0, NewtonIter:  1
      ( R ) = ( 2.05e-14 ) ;
      Last LinSolve(iter,res) = (  67, 5.61e-11 ) ;
  SinglePhaseFlow: Newton solver converged in less than 4 iterations, time-step required will be doubled.
  Cleaning up events
  Umpire            HOST sum across ranks:   14.8 MB
  Umpire            HOST         rank max:   14.8 MB
  total time                         5.658s
  initialization time                0.147s
  run time                           3.289s


All newton iterations are logged along with corresponding nonlinear residuals for each time iteration.
In turn, for each newton iteration, `LinSolve`` provides the number of linear iterations and the final residual reached by the linear solver.
Information on run times, initialization times, and maximum amounts of
memory (high water mark) are given at the end of the simulation, if successful.


Congratulations on completing this first run!



------------------------------------