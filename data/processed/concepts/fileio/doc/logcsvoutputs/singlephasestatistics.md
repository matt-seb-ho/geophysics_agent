**Context:** Fileio > Doc > LogCsvOutputs > SinglePhaseStatistics

## SinglePhaseStatistics
### Single-phase simulation statistics
This component manages and computes statistics for single-phase fluid simulations. The output provides the following information for a given wrapper [1]_, for a given region at a given time:

- **Pressure [Pa]:**

  Minimum, average and maximum pressure for this region.

- **Delta pressure [Pa]:**

  Pressure change in the reservoir since the start of the simulation.

- **Temperature [K]:**

  Minimum, average and maximum temperature for this region.

- **Total dynamic pore volume [rm³]:**

  Total pore volume occupied by fluids in the rock. This value is dynamic and depends on pressure.

- **Total fluid mass [kg or mol]:**

  Total mass of fluid present in the given region.

The output can be saved in the log file if this option is specified (as mentioned [here ](#how-to-generate-these-outputs)_).
You can find more information about the log option [here ](https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/datastructure/SinglePhaseStatistics.html)_.

.. [1]

   A wrapper is a tool that makes a software component (such as a material model or a solver) accessible and configurable from input files. It is used to connect the internals of the GEOS code with what users can see, modify and use. For example, CompositionalMultiphaseFVM is a solver and its associated wrapper allows configuration via input files. See the [Wrapper ](https://geosx-geosx.readthedocs-hosted.com/en/latest/coreComponents/dataRepository/docs/Wrapper.html?_sm_au_=iVVFWf2SqSTnZPfQQ0WpHK6H8sjL6)_ page for more information.
