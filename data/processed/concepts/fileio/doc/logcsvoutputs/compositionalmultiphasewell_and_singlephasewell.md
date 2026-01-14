**Context:** Fileio > Doc > LogCsvOutputs > CompositionalMultiphaseWell and SinglePhaseWell

## CompositionalMultiphaseWell and SinglePhaseWell
### Modeling multiphase or single-phase flow in wells
The CSV file generated (if enabled) contains information on a well's production rates for several phases and associated parameters at each recorded time step. A CSV file is generated for each well and for each time step.

The files provide the following information:

- **Time [s]:** The current simulation time.

- **dt [s]:** The time interval used for this step. (Not available for [SinglePhaseWell`.)

- **BHP [Pa]:** Bottom hole pressure at the reference depth.

- **Total rate [kg/s]:** Total mass flow produced or injected by the well at the current time.

For `SinglePhaseWell`:

- **Total reservoir volumetric rate [rm³/s]:** Total volumetric flow at reservoir conditions (enabled if `useSurfaceCondition="0"` on `WellControls`).
- **Total surface volumetric rate [sm³/s]:** Total volumetric flow at surface conditions (enabled if `useSurfaceCondition="1"`).

For `CompositionalMultiphaseWell`:

- **Total reservoir volumetric rate [rm³/s]:** Total volumetric flow at reservoir conditions.
- **Phase i reservoir volumetric rate [rm³/s]:** Volume flow rate of phase i (e.g., oil, gas, water) at reservoir conditions (enabled if `useSurfaceCondition="0"`).
- **Phase i surface volumetric rate [sm³/s]:** Volume flow of phase i at surface conditions (enabled if `useSurfaceCondition="1"`).

The output can be saved in the log file and/or a CSV file if these options are specified (as mentioned `here ](#how-to-generate-these-outputs)_). More information is available [here ](https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/datastructure/CompositionalMultiphaseWell.html)_ and [here ](https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/datastructure/SinglePhaseWell.html)_.

If the CSV file contains 0.0 values for BHP, total_rate, total_vol_rate or phaseN_vol_rate, the well is shut; the log file will indicate this with "wellName: well is shut".

Certain error messages are added to the log when invalid well parameter combinations are detected (for example, defining a phase rate for a single-phase well is forbidden).

Both components have similar outputs; CompositionalMultiphaseWell includes values for each phase's volumetric rate, while SinglePhaseWell reports only the single phase present.

