**Context:** Buildguide > Prerequisites > List of prerequisites

## List of prerequisites
Minimal requirements:

- [CMake ](https://cmake.org/) build system generator (3.23.1+).
- build tools ([GNU make ](https://www.gnu.org/software/make/) or [ninja ](https://ninja-build.org/) on Linux, XCode on MacOS).
- a C++ compiler with full c++17 standard support ([gcc ](https://gcc.gnu.org/) 12+ or [clang ](https://clang.llvm.org/) 13.0+ are recommended).
- [python ](https://www.python.org/) 3.9-3.11 (versions 3.12+ are untested).
- :code:[zlib`, :code:`blas` and :code:`lapack` libraries
- any compatible MPI runtime and compilers (if building with MPI)

If you want to build from a repository check out (instead of a release tarball):

- `git ](https://git-scm.com/) (2.20+ is tested, but most versions should work fine)

If you plan on building bundled third-party library (TPLs) dependencies yourself:

- Compatible C and Fortran compilers

If you will be checking out and running integrated tests (a submodule of GEOS, currently not publicly available):

- [git-lfs ](https://git-lfs.github.com/) (Git Large File Storage extension)
- [h5py ](https://www.h5py.org/) and [mpi4py ](https://pypi.org/project/mpi4py/) python modules

If you are interested in building Doxygen documentation:

- [GNU bison ](https://www.gnu.org/software/bison/)
- [LaTeX ](https://www.latex-project.org/)
- [ghostscript ](https://www.ghostscript.com/)
- [Graphviz ](https://graphviz.org/)

In order for XML validation to work (executed as an optional build step):

- [xmllint ](http://xmlsoft.org/xmllint.html)
