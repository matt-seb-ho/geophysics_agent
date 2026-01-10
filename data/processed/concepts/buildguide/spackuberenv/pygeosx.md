**Context:** Buildguide > SpackUberenv > pygeosx

## pygeosx


It is worth noting that GEOS has `two project json files ](https://uberenv.readthedocs.io/en/latest/#project-configuration) ([.uberenv_config.json` and `scripts/pygeosx_configs/pygeosx.json`) and two configuration directories for LC systems (`scripts/spack_configs` and `scripts/pygeosx_configs`). The `.uberenv_config.json` project json file and `scripts/spack_configs` directory is for building GEOS dependencies. The `scripts/pygeosx_configs/pygeosx.json` project json file and `scripts/pygeosx_configs` directory is for building `pygeosx` dependencies.This is because `pygeosx` has a separate list of required compilers and packages to build from GEOS (e.g. `pygeosx`'s numpy dependency recommends building with gcc and using openblas for BLAS/LAPACK). When not building `pygeosx`, other dependencies of GEOS still depend on python. An existing system version of python will work just fine, and can be put in GEOS's `spack.yaml` to prevent Spack from building its own verion of python. By default, Uberenv will find and use `.uberenv_config.json` to build GEOS, but you can use the `--project-json` command line option to target `scripts/pygeosx_configs/pygeosx.json` to build `pygeosx`:

``console
    ./scripts/uberenv/uberenv.py --spack-config-dir=/path/to/your/config/directory/ --spec="%clang@14.0.6" --project-json="scripts/pygeosx_configs/pygeosx.json"




.. _BuildConfig:
