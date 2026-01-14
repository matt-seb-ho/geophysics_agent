**Context:** Developerguide > Contributing > Benchmarks > Specifying a benchmark

## Specifying a benchmark
A group of benchmarks is specified with a standard GEOS input XML file with an extra `Benchmarks` block added at the top level. This block is ignored by GEOS itself and only used by the `runBenchmarks.py` script.


   :language: xml
   :start-after: <Problem>
   :end-before: <Solvers>

*[Source: benchmarks/SSLE-small.xml]*

The `Benchmarks` block consists of a block for each machine the benchmarks are to run on. Currently the only options are `quartz`, `lassen`, and `crusher`.


#### The `Run` block
Each machine block contains a number of `Run` blocks each of which specify a family of benchmarks to run. Each `Run` block must have the following required attributes

  - `name`: The name of the family of benchmarks, must be unique among all the other `Run` blocks on that system.
  - `nodes`: An integer which specifies the base number of nodes to run the benchmark with.
  - `tasksPerNode`: An integer that specifies the number of tasks to launch per node.

Each `Run` block may contain the following optional attributes

  - `threadsPerTask`: An integer specifying the number of threads to allocate each task.
  - `timeLimit`: An integer specifying the time limit in minutes to pass to the system scheduler when submitting the benchmark.
  - `args`: containing any extra command line arguments to pass to GEOS.
  - `autoPartition`: Either `On` or `Off`, not specifying `autoPartition` is equivalent to `autoPartition="Off"`. When auto partitioning is enabled the script will compute the number of `x`, `y` and `z` partitions such that the the resulting partition is close to a perfect cube as possible, ie with 27 tasks `x = 3, y = 3, z = 3` and with 36 tasks `x = 4, y = 3, z = 3`. This is optimal when the domain itself is a cube, but will be suboptimal otherwise.
  - `strongScaling`: A list of unique integers specifying the factors to scale the number of nodes by. If `N` number are provided then `N` benchmarks are run and benchmark `i` uses `nodes * strongScaling[ i ]` nodes. Not specifying `strongScaling` is equivalent to `strongScaling="{ 1 }"`.

Looking at the example `Benchmarks` block above on Lassen one benchmark from the `OMP_CUDA` family will be run with one node and one task. Four benchmarks from the `MPI_OMP_CUDA` family will be run with one, two, four and eight nodes and four tasks per node.

Note that specifying a time limit for each benchmark family can greatly decrease the time spent waiting in the scheduler's queue. A good rule of thumb is that the time limit should be twice as long as it takes to run the longest benchmark in the family.

