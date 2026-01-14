**Context:** Fileio > Doc > LogCsvOutputs > How to generate these outputs

## How to generate these outputs
In order to generate these outputs, you must specify them in the input files.

### CSV outputs
To generate a CSV output, specify `writeCSV="1"` as follows``
    <Tasks>

      <CompositionalMultiphaseStatistics
        name="compflowStatistics"
        flowSolverName="compflow"
        logLevel="1"
        writeCSV="1"
        computeCFLNumbers="1"
        computeRegionStatistics="1"/>
      
    </Tasks>

If you do not want CSV output, do not add the `writeCSV` attribute.

### Log outputs
To generate a log output, specify `logLevel="x"`, where `x` can be 0, 1, 2, 3, 4 or 5, for example``
    <Tasks>
      <CompositionalMultiphaseStatistics
        name="compflowStatistics"
        flowSolverName="compflow"
        logLevel="1"
        computeCFLNumbers="1"
        computeRegionStatistics="1"/>
    </Tasks>

If you do not want log output, do not add the [logLevel` attribute.

Depending on the value of the `logLevel` parameter and the associated component, different levels of detail are available in the statistics displayed. To find the appropriate value for `logLevel`, refer to the GEOS documentation for the associated component.
