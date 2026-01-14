**Context:** Developerguide > Contributing > IntegratedTests > Machine Definitions

## Machine Definitions
On many machines, ATS will automatically identify your machine's configuration and optimize it's performance.
If the tests fail to run or to properly leverage your machine's resources, you may need to manually configure the machine.
If you know the appropriate name for your machine in ATS (or the geos_ats package), then you can run `./geos_ats.sh --machine machine_name --ats help` to see a list of potential configuration options.

The `openmpi` machine is a common option for non-LC systems.
For a system with 32 cores/node, an appropriate run command might look like:

```sh
  ./geos_ats.sh --machine openmpi --ats openmpi_numnodes 32 --ats openmpi_args=--report-bindings --ats openmpi_args="--bind-to none" --ats openmpi_install "/path/to/openmpi/installation"







