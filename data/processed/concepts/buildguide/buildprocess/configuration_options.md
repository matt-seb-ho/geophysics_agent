**Context:** Buildguide > BuildProcess > Configuration options

## Configuration options
Below is a list of CMake configuration options, in addition to TPL options above.
Some options, when enabled, require additional settings (e.g. `ENABLE_CUDA``).
Please see `host-config examples ](https://github.com/GEOS-DEV/GEOS/blob/develop/host-configs).

=============================== ========= ==============================================================================
Option                          Default   Explanation
=============================== ========= ==============================================================================
`ENABLE_MPI`                  `ON`    Build with MPI (also applies to TPLs)
`ENABLE_OPENMP`               `OFF`   Build with OpenMP (also applies to TPLs)
`ENABLE_CUDA`                 `OFF`   Build with CUDA (also applies to TPLs)
`ENABLE_CUDA_NVTOOLSEXT`      `OFF`   Enable CUDA NVTX user instrumentation (via GEOS_MARK_SCOPE or GEOS_MARK_FUNCTION macros)
`ENABLE_HIP`                  `OFF`   Build with HIP/ROCM (also applies to TPLs)
`ENABLE_DOCS`                 `ON`    Build documentation (Sphinx and Doxygen)
`ENABLE_WARNINGS_AS_ERRORS`   `ON`    Treat all warnings as errors
`ENABLE_PVTPackage`           `ON`    Enable PVTPackage library (required for compositional flow runs)
`ENABLE_TOTALVIEW_OUTPUT`     `OFF`   Enables TotalView debugger custom view of GEOS data structures
`ENABLE_COV`                  `OFF`   Enables code coverage
`GEOS_ENABLE_TESTS`           `ON`    Enables unit testing targets
`GEOS_LA_INTERFACE`           `Hypre` Choiсe of Linear Algebra backend (Hypre/Petsc/Trilinos)
`GEOS_BUILD_OBJ_LIBS`         `ON`    Use CMake Object Libraries build
`GEOS_BUILD_SHARED_LIBS`      `OFF`   Build `geosx_core` as a shared library instead of static
`GEOS_PARALLEL_COMPILE_JOBS`            Max. number of compile jobs (when using Ninja), in addition to `-j` flag
`GEOS_PARALLEL_LINK_JOBS`               Max. number of link jobs (when using Ninja), in addition to `-j` flag
`GEOS_INSTALL_SCHEMA`         `ON`    Enables schema generation and installation
=============================== ========= ==============================================================================
