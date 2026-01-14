**Context:** Buildguide > SpackUberenv > Build Configuration

## Build Configuration


The GEOS Spack package has a lot of options, or what Spack calls variants, for controlling which dependencies you would like to build and how you'd like them built. The `GEOS Spack package file  ](https://github.com/GEOS-DEV/thirdPartyLibs/blob/master/scripts/spack_packages/packages/geosx/package.py) has variants that are marked with [variant()` in the file.

For example if you wanted to build with the GCC 12.1.1 compiler toolchain, without Caliper and with Hypre as the Linear Algebra Interface, your spec would be `~caliper lai=hypre %gcc-12`, variants followed by the compiler toolchain.

The GEOS Spack package lists out the libraries that GEOS depends ons. These dependencies are marked with `depends_on()` in the file.

Using the Spack spec syntax, you can inturn specify variants for each of the dependencies of GEOS. For example, you could modify the spec above to build RAJA in debug mode by using `~caliper lai=hypre %gcc@10.3.1 ^raja build_type=Debug`. When building with Uberenv, Spack should print out a table containing the full spec for every dependency it will build. If you would like to look at the variants for say RAJA in more detail, you can find the package file at `uberenv_libs/spack/var/spack/repos/builtin/packages/raja/package.py`, by using `file finder ](https://docs.github.com/en/get-started/accessibility/keyboard-shortcuts#source-code-browsing) on the [Spack Packages Github website ](https://github.com/spack/spack-packages), or by searching for the package at https://packages.spack.io/.


.. _HostConfig:
