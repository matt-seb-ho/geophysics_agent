**Context:** Buildguide > BuildProcess > Build steps

## Build steps
- Create a host-config file that sets all system-specific CMake variables.
  Take a look at [host-config examples ](https://github.com/GEOS-DEV/GEOS/blob/develop/host-configs).
  We recommend the same host-config is used for both TPL and GEOS builds.
  In particular, certain options (such as `ENABLE_MPI` or `ENABLE_CUDA`) need to match between the two.

- Provide paths to all enabled TPLs.
  This can be done in one of two ways:

  * Provide each path via a separate CMake variable (see :ref:`Dependencies` for path variable names).
  * If you built TPLs from the `tplMirror` repository, you can set `GEOSX_TPL_DIR` variable in your host-config to point to the TPL installation path, and

    ``cmake
       include("/path/to/GEOS/host-configs/tpls.cmake")

    which will set all the individual TPL paths for you.

- Configure via `config-build.py` script:

  ``console
     cd GEOS
     python scripts/config-build.py --hostconfig=/path/to/host-config.cmake --buildtype=Release --installpath=/path/to/install/dir

  where

  * `--buildpath` or `-bp` is the build directory (by default, created under current working dir).
  * `--installpath` or `-ip` is the installation directory(wraps `CMAKE_INSTALL_PREFIX`).
  * `--buildtype` or `-bt` is a wrapper to the `CMAKE_BUILD_TYPE` option.
  * `--hostconfig` or `-hc` is a path to host-config file.
  * all unrecognized options are passed to CMake.

  If `--buildpath` is not used, build directory is automatically named `build-<config-filename-without-extension>-<buildtype>`.
  It is possible to keep automatic naming and change the build root directory with `--buildrootdir`.
  In that case, build path will be set to `<buildrootdir>/<config-filename-without-extension>-<buildtype>`.
  Both `--buildpath` and `--buildrootdir` are incompatible and cannot be used in the same time.
  Same pattern is applicable to install path, with `--installpath` and `--installrootdir` options.

- Run the build:

  ``console
     cd <buildpath>
     make -j $(nproc)

You may also run the CMake configure step manually instead of relying on [config-build.py`.
A full build typically takes between 10 and 30 minutes, depending on chosen compilers, options and number of cores.
