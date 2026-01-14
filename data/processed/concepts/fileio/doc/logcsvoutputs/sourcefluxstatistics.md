**Context:** Fileio > Doc > LogCsvOutputs > SourceFluxStatistics

## SourceFluxStatistics
### Production and injection statistics by region
This section explains how global statistics on boundary flow conditions are calculated. These conditions generally represent injection or production wells applied to zones of the simulated domain such as fractures or reservoir zones. The table provides the following information:

- **Produced mass [kg or mol]:**

  Amount of fluid produced by the flux (one value per fluid phase). It is defined with the `scale` attribute:

  - If `scale = 0`, nothing happens.
  - If `scale < 0[, an injection is performed; the injected amount equals the product of the rate and the scaling factor.
  - If `scale > 0`, a production is performed; the produced amount equals the product of the rate and the scaling factor.

- **Production rate [kg/s or mol/s]:**

  Production rate for the flux (one value per fluid phase). Also defined with the `scale` attribute (same semantics as above).

- **Element Count:**

  Number of mesh cells directly affected by the source (injection or production); used in flux statistics computation.

The output can be saved in the log file and/or a CSV file if the associated options are specified (as mentioned `here ](#how-to-generate-these-outputs)_). If the CSV option is enabled, the start of the statistical measurement period is included in the table. More details are available [here ](https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/datastructure/SourceFluxStatistics.html#:~:text=When%20set%20to%201%2C%20write%20the%20statistics%20into%20a%20CSV%20file)_.
