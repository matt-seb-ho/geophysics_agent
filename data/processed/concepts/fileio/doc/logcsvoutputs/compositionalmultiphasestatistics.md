**Context:** Fileio > Doc > LogCsvOutputs > CompositionalMultiphaseStatistics

## CompositionalMultiphaseStatistics
### Regional statistics for a multiphase simulation of CO2
This component computes specific statistics for defined regions in a mesh during a CO2 injection simulation. At each simulation timestep, the following quantities are reported:

- **Pressure [Pa]:**

  Minimum, average and maximum pressure for the region.

- **Delta pressure [Pa]:**

  Pressure change in the reservoir since the start of the simulation.

- **Temperature [K]:**

  Minimum, average and maximum temperature for the region.

- **Total dynamic pore volume [rm³]:**

  Total pore volume occupied by all phases combined. This value is dynamic and depends on pressure.

- **Phase dynamic pore volume [rm³]:**

  Pore volume available for each phase.

- **Phase mass [kg or mol]:**

  Mass or number of moles of fluid present for each phase.

- **Metric 1 (based on the fluid's ability to be trapped or not, regardless of its actual mobility)**

  - **Trapped phase mass [kg or mol]:** For each phase, mass or number of moles that are immobile because they are trapped in the porous structure.

  - **Non-trapped phase mass [kg or mol]:** For each phase, potentially mobile mass or number of moles (not trapped, but not necessarily in motion).

- **Metric 2 (based on the effective mobility of the fluid in the system)**

  - **Immobile phase mass [kg or mol]:** For each phase, mass or number of moles that do not move in the simulation (for example due to trapping, viscosity, or pressure thresholds).

  - **Mobile phase mass [kg or mol]:** For each phase, mass or number of moles that is in motion or can move depending on simulation conditions.

- **Component mass [kg or mol]:**

  For each phase, mass or number of moles of each component, enabling assessment of mixture composition.

The output can be saved in the log file and/or a CSV file if these options are specified (as mentioned [here ](#how-to-generate-these-outputs)_) when the program is run. More information about log and CSV options is available [here ](https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/datastructure/CompositionalMultiphaseStatistics.html)_.


