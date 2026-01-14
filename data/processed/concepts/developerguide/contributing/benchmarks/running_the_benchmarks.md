**Context:** Developerguide > Contributing > Benchmarks > Running the benchmarks

## Running the benchmarks
Because performance is system specific we currently only support running the benchmarks on the LLNL machines Quartz and Lassen. If you are on either of these machines the script `benchmarks/runBenchmarks.py` can be used to run the benchmarks.

``
    > python ../benchmarks/runBenchmarks.py --help
    usage: runBenchmarks.py [-h] [-t TIMELIMIT] [-o TIMINGCOLLECTIONDIR]
                            [-e ERRORCOLLECTIONDIR]
                            geosxPath outputDirectory

    positional arguments:
      geosxPath             The path to the GEOS executable to benchmark.
      outputDirectory       The parent directory to run the benchmarks in.

    optional arguments:
      -h, --help            show this help message and exit
      -t TIMELIMIT, --timeLimit TIMELIMIT
                            Time limit for the entire script in minutes, the
                            default is 60.
      -o TIMINGCOLLECTIONDIR, --timingCollectionDir TIMINGCOLLECTIONDIR
                            Directory to copy the timing files to.
      -e ERRORCOLLECTIONDIR, --errorCollectionDir ERRORCOLLECTIONDIR
                            Directory to copy the output from any failed runs to.

At a minimum you need to pass the script the path to the GEOS executable and a directory to run the benchmarks in. This directory will be created if it doesn't exist. The script will collect a list of benchmarks to be run and submit a job to the system's scheduler for each benchmark. This means that you don't need to be in an allocation to run the benchmarks. Note that this is different from the integrated tests where you need to already be in an allocation and an internal scheduler is used to run the individual tests. Since a benchmark is a measure of performance to get consistent results it is important that each time a benchmark is run it has access to the same resources. Using the system scheduler guarantees this.

In addition to whatever outputs the input would normally produce (plot files, restart files, ...) each benchmark will produce an output file `output.txt` containing the standard output and standard error of the run and a `.cali` file containing the Caliper timing data in a format that Spot_ can read.


