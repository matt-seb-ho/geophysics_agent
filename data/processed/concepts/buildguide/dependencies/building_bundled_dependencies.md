**Context:** Buildguide > Dependencies > Building bundled dependencies

## Building bundled dependencies
To simplify the process of building TPLs, we provide a git repository [thirdPartyLibs ](https://github.com/GEOS-DEV/thirdPartyLibs).
It contains source copies of exact TPL versions required and is updated periodically.
It also contains a CMake script for building all TPLs in a single command.

The recommended steps to build TPLs are:

- Create a host-config file that sets all system-specific CMake variables (compiler and library paths, configuration flags, etc.)
  Take a look at [host-config examples ](https://github.com/GEOS-DEV/GEOS/blob/develop/host-configs).
- Configure via `config-build.py` script:

  ``console
     cd thirdPartyLibs
     python scripts/config-build.py --hostconfig=/path/to/host-config.cmake --buildtype=Release --installpath=/path/to/install/dir -DNUM_PROC=8

  where

  * `--buildpath` or `-bp` is the build directory (by default, created under current).
  * `--installpath` or `-ip` is the installation directory(wraps `CMAKE_INSTALL_PREFIX`).
  * `--buildtype` or `-bt` is a wrapper to the `CMAKE_BUILD_TYPE` option.
  * `--hostconfig` or `-hc` is a path to host-config file.
  * all other command-line options are passed to CMake.

- Run the build:

  ``console
     cd <buildpath>
     make

  
     Instead use `-DNUM_PROC` option above, which is passed to each sub-project's `make` command.

You may also run the CMake configure step manually instead of relying on `config-build.py`.
The full TPL build may take anywhere between 15 minutes and 2 hours, depending on your machine, number of threads and libraries enabled.




   If you do not have access to internet, modify the [./configure` step of petsc in `CMakeLists.txt` and change the `--download-ptscotch` option accordingly.
   `pt-scotch` also relies on `bison` and `flex`.
