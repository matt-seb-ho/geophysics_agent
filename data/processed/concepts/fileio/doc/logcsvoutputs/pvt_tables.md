**Context:** Fileio > Doc > LogCsvOutputs > PVT Tables

## PVT Tables
PVT tables define fluid properties as a function of pressure and temperature. They are integrated into fluid and relative-permeability models to enable accurate multiphase flow simulations. An application example is available [here ](https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/basicExamples/co2Injection/Example.html#constitutive-laws)_.

- **CO2BrinePhillipsFluid:**

  Models properties of CO2–brine mixtures, including CO2 solubility in brine as a function of pressure and temperature.

- **ReactiveBrineFluid:**

  Models reactions between brine and rock, including pressure and temperature effects.

- **CO2BrineEzrokhiFluid:**

  Models CO2–brine properties (density, viscosity) without salinity effects, suitable when salinity is negligible.

Generated PVT tables contain data on the physical properties of fluids across a user-specified range of pressures and temperatures. These tables can be written to the log and/or CSV files when the corresponding options are enabled.

The output for each temperature/pressure combination contains:

- Pressure [Pa]
- Temperature [K]
- CO2 solubility [g/L]
- H2O solubility [g/L]