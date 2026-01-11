**Context:** Buildguide > ContinuousIntegration > Building docker images

## Building docker images
Our continuous integration process builds the TPL and GEOS against two operating systems (ubuntu and centos) and two compilers (clang and gcc).
The docker files use [multi-stage builds ](https://docs.docker.com/develop/develop-images/multistage-build/) in order to minimise the sizes of the images.

* First stage installs and defines all the elements that are commons to both TPL and GEOS (for example, MPI and c++ compiler, BLAS, LAPACK, path to the installation directory...).
* As a second stage, we install everything needed to build (`not run`) the TPLs.
  We keep nothing from this second step for GEOS, except the compiled TPL themselves.
  For example, a fortran compiler is needed by the TPL but not by GEOS: it shall be installed during this step, so GEOS won't access a fortran compiler (it does not have to).
* Last stage copies the compiled TPL from second stage and installs the elements only required by GEOS (there are few).

.. _Docker_images_contract:
