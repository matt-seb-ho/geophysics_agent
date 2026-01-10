**Context:** Fileio > Doc > LogCsvOutputs > TableFunction

## TableFunction
### Defining variable properties
This component manages tabulated functions: properties that vary in space or time (for example, pressure or temperature vs. depth). The component interpolates data provided as table pairs and applies them to mesh entities during simulation.

If the table contains 1D or 2D data it can be displayed directly in the log file. It is also possible to save this data to a CSV file if that option is enabled. If the table contains 3D data or higher dimensions, a CSV file will be generated containing all the data; the logs will contain a message indicating the CSV file location. If the table is too large (more than 500 points) and you asked for log display, the data will not be shown in the logs — consult the generated CSV file instead.
