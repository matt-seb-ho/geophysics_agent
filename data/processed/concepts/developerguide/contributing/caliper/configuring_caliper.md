**Context:** Developerguide > Contributing > Caliper > Configuring Caliper

# Configuring Caliper
Caliper configuration is done by specifying a string to initialize Caliper with via the
`-t` option. A few options are listed below but we refer the reader to
`Caliper Config ](https://software.llnl.gov/Caliper/BuiltinConfigurations.html) for the full Caliper tutorial.

* [-t runtime-report,max_column_width=200` Will make Caliper print aggregated timing information to standard out, with a column width large enought that it doesn't truncate most function names.
* `-t runtime-report,max_column_width=200,profile.cuda` Does the same as the above, but also instruments CUDA API calls. This is only an option when building with CUDA.
* `-t runtime-report,aggregate_across_ranks=false` Will make Caliper write per rank timing information to standard out. This isn't useful when using more than one rank but it does provide more information for single rank runs.
* `-t spot()` Will make Caliper output a `.cali` timing file that can be viewed in the Spot web server.

