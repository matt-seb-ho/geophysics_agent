**Context:** Buildguide > ContinuousIntegration > Docker images contract

## Docker images contract
GEOS will find a compiled version of the third party libraries.

As part of the contract provided by the TPL, the docker images also defines several environment variables.
The

``sh
    GEOS_TPL_DIR

variable contains the absolute path of the installation root directory of the third party libraries.
GEOS must use it when building.

Other variables are classical absolute path compiler variables.

``sh
    CC
    CXX
    MPICC
    MPICXX

And the absolute path the mpirun (or equivalent) command.

``sh
    MPIEXEC

The following `openmpi` environment variables allow it to work properly in the docker container.
But there should be no reason to access or use them explicitly.

``sh
    OMPI_CC=$CC
    OMPI_CXX=$CXX
