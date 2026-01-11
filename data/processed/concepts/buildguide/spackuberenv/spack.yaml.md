**Context:** Buildguide > SpackUberenv > spack.yaml

## spack.yaml
The [spack.yaml` configuration file tells Spack where it can find relevant packages and compilers to build GEOS third-party dependencies. Without `spack.yaml`, building the dependencies will take significantly longer.

There are many examples and resources available for constructing a `spack.yaml` file:

* GEOS's LC configuration files for `toss_4_x86_64_ib ](https://github.com/GEOS-DEV/thirdPartyLibs/blob/master/scripts/spack_configs/toss_4_x86_64_ib/spack.yaml) and [toss_4_x86_64_ib_cray ](https://github.com/GEOS-DEV/thirdPartyLibs/blob/master/scripts/spack_configs/toss_4_x86_64_ib_cray/spack.yaml). Additionally, the header of these configuration files include the Spack spec to pass to [--spec` for different compiler toolchains and package variants.
* LLNL's shared Spack configurations for RADIUSS projects: https://github.com/LLNL/radiuss-spack-configs/tree/main
* NERSC Spack Infrastructure: https://github.com/NERSC/spack-infrastructure/tree/main
* Shared Spack configuration files with other HPC sites: https://github.com/spack/spack-configs
* The documentation list mentioned above: :ref:`SpackUberenv`

### spack.yaml from scratch
If the examples and resources listed in :ref:`SpackYaml` are not applicable to your system, or you would like to see what packages are already installed on your system, you can call Uberenv with the following option:

``console
    ./scripts/uberenv/uberenv.py --setup-and-env-only

This command will setup Spack and ask Spack create a `spack.yaml`` environment file for you. Uberenv will invoke `spack compiler find ](https://spack.readthedocs.io/en/latest/getting_started.html#compiler-configuration) and [spack external find ](https://spack.readthedocs.io/en/latest/packages_yaml.html#automatically-find-external-packages) to find pre-installed compilers and packages on your system.



  This command should be used as a first approximation of your system environment, to determine the paths where more suitable compilers and packages are potentially located.

### Required package versions in versions.yaml
In the LC configuration file `versions.yaml ](https://github.com/GEOS-DEV/thirdPartyLibs/blob/master/scripts/spack_configs/versions.yaml) , you will see a list of packages with the [require` keyword:

```console
  hypre:
    require: "@git.06da35b1a4b1066a093bc0c6c48aee12bee74cd4"
  ...

This tells Spack that GEOS always `requires ](https://spack.readthedocs.io/en/latest/packages_yaml.html#requirements-syntax) a specific commit of [hypre`, a commit on the latest develop branch in this case. Ideally, package versions should be specified in the `GEOS Spack package file  ](https://github.com/GEOS-DEV/thirdPartyLibs/blob/master/scripts/spack_packages/packages/geosx/package.py). However, when a version of a package is newer than what Spack knows about or an unversioned commit is needed, the Spack package syntax cannot express that requirement. As a result:




