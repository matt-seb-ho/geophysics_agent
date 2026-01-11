**Context:** QuickStart > Compiling the TPLs

## Compiling the TPLs
.. note``
   If you are working on an HPC system with other GEOS developers, check with them to see if the TPLs have already been compiled in a shared directory. If this is the case, you can skip ahead to just compiling the main code.
   If you are working on your own machine, you will need to configure and compile both the TPLs and the main code.

We begin by configuring the third-party libraries (TPLs) using the `config-build.py` script. This script sets up the build directory and runs CMake to generate the necessary build files.

``sh
   cd thirdPartyLibs
   python scripts/config-build.py -hc ../GEOS/host-configs/your-platform.cmake -bt Release

The TPLs will be configured in a build directory named consistently with your host configuration file, i.e., `build-your-platform-release`.

``sh
   cd build-your-platform-release
   make

.. note``
   Building all of the TPLs can take quite a while, so you may want to go get a cup of coffee at this point.
   Also note that you should *not* use a parallel `make -j N` command to try and speed up the build time.
