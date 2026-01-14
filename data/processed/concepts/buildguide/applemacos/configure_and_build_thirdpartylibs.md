**Context:** Buildguide > AppleMacOS > Configure and build thirdPartyLibs

## Configure and build thirdPartyLibs
.. code-block``
  python3 scripts/config-build.py -hc ../GEOS/host-configs/apple/macOS_arm.cmake -bt Release

You will get a warning you can ignore

.. code-block``
  CMake Warning at /Users/settgast1/Codes/geos/GEOS/host-configs/tpls.cmake:10 (message):
    'GEOS_TPL_DIR' does not exist.


Continue with the build

.. code-block``
  cd build-macOS_arm-release
  make

You will get an error at the end...you can ignore it.

.. code-block``
  [100%] Linking CXX executable ../../../tests/blt_mpi_smoke
  ld: warning: -commons use_dylibs is no longer supported, using error treatment instead
  ld: file not found: @rpath/libquadmath.0.dylib for architecture arm64
  clang: error: linker command failed with exit code 1 (use -v to see invocation)
  make[2]: *** [tests/blt_mpi_smoke] Error 1
  make[1]: *** [blt/tests/smoke/CMakeFiles/blt_mpi_smoke.dir/all] Error 2
  make: *** [all] Error 2

