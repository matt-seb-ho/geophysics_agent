**Context:** Developerguide > Contributing > UnitTests > MPI

## MPI
Often times it makes sense to write a unit test that is meant to be run with multiple MPI ranks. This can be accomplished by simply adding the `NUM_MPI_TASKS` parameter to `geos_add_test` in the CMake file. For example

``
  geos_add_test( NAME testWithMPI
                 COMMAND testWithMPI
                 NUM_MPI_TASKS ${NUMBER_OF_MPI_TASKS} )

With this addition `make test` or calling `ctest` directly will run `testWithMPI` via something analogous to `mpirun -n NUMBER_OF_MPI_TASKS testWithMPI``.
