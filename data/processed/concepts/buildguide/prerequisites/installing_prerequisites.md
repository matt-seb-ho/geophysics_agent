**Context:** Buildguide > Prerequisites > Installing prerequisites

## Installing prerequisites
On a local development machine with sudo/root privileges, most of these dependencies can be installed with a system package manager.
For example, on a Debian-based system (check your package manager for specific package names):

[``console
    sudo apt install build-essential git git-lfs gcc g++ gfortran cmake libopenmpi-dev libblas-dev liblapack-dev zlib1g-dev python3 python3-h5py python3-mpi4py libxml2-utils

On HPC systems it is typical for these tools to be installed by system administrators and provided via `modules ](http://modules.sourceforge.net/).
To list available modules, type:

```console
    module avail

Then load the appropriate modules using :code:`module load` command.
Please contact your system administrator if you need help choosing or installing appropriate modules.
