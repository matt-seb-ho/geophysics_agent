**Context:** QuickStart > Defining a Host-Config File

## Defining a Host-Config File
GEOS compilations are driven by a CMake `host-config` file, which informs the build system about the compilers you are using, where various packages reside, and what options you want to enable. 

A template for creating a simple `host-config` is provided in `host-configs/quick-start-template.cmake`.


   :language: sh

The various `set()` commands are used to set variables that control the build. To begin, make a copy of the template file and modify the paths according to the installation locations on your system. 

We have created a number of default host-config files for common systems. You should browse them to see if any are close to your needs:
We maintain host configuration files (ending in `.cmake`) for HPC systems at various institutions, as well as for common personal systems. 
If you cannot find one that matches your needs, we suggest starting with one of the shorter ones and modifying it as needed. 



# Compilation
The configuration process for both the third-party libraries (TPLs) and GEOS is managed through a Python script called `config-build.py`. This script simplifies and automates the setup by configuring the build and install directories and by running CMake based on the options set in the host-config file 
which is passed as a command-lne argument. The `config-build.py` script has several command-line options. Here, we will only use some basic options and rely on default values for many others. During this build process there wil be automatically generated build and install directories for both the TPLs and the main code,
with names consistent with the name specified in the host-config by the variable `CONFIG_NAME`, i.e. `build-your-platform-release` and `install-your-platform-release`. 

All options can be visualized by running

``sh
   cd thirdPartyLibs
   python scripts/config-build.py -h

.. note``
   It is strongly recommended that GEOS and TPLs be configured using the same host configuration file. Below, we assume that you keep this file in, for example, `GEOS/host-configs/your-platform.cmake`, but the exact location is up to you.
