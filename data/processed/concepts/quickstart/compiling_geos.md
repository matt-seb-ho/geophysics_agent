**Context:** QuickStart > Compiling GEOS

## Compiling GEOS
Once the TPLs have been compiler, the next step is to compile the main code. The `config-build.py` script is used to configure the build directory. Before running the configuration script, ensure that the path to the TPLs is correctly set in the host configuration file by setting

``sh
   set(GEOS_TPL_DIR "/path/to/your/TPL/installation/dir" CACHE PATH "")

If you have followed these instructions, the TPLs are installed at the default location, i.e. `/path/to/your/TPL/thirdPartyLibs/install-your-platform-release`.

``sh
   cd ../../GEOS
   python scripts/config-build.py -hc host-configs/your-platform.cmake -bt Release

An alternative is to set the path `GEOS_TPL_DIR` via a cmake command line option, e.g.

``sh
   python scripts/config-build.py -hc host-configs/your-platform.cmake -bt Release -D GEOS_TPL_DIR=/full/path/to/thirdPartyLibs

.. note``
   We highly recommend using full paths, rather than relative paths, whenever possible.

Once the configuration process is completed, we proceed with the compilation of the main code and the instalation of geos.  

``sh
   cd build-your-platform-release
   make -j4
   make install   

The parallel `make -j 4` will use four processes for compilation, which can substantially speed up the build if you have a multi-processor machine.
You can adjust this value to match the number of processors available on your machine.
The `make install` command then installs GEOS to a default location unless otherwise specified.

If all goes well, a `geosx` executable should now be available

``sh
  GEOS/install-your-platform-release/bin/geosx

# Running
We can do a quick check that the geosx executable is working properly by calling the executable with our help flag

``sh
  ./bin/geosx --help

This should print out a brief summary of the available command line arguments:

``sh
    USAGE: geosx -i input.xml [options]
           geosx -s schema-output.xml

    Options:
    -?, --help
    -i, --input,             Input xml filename (required)
    -r, --restart,           Target restart filename
    -x, --x-partitions,      Number of partitions in the x-direction
    -y, --y-partitions,      Number of partitions in the y-direction
    -z, --z-partitions,      Number of partitions in the z-direction
    -s, --schema,            Name of the output schema
    -v, --validate-input,    only do the loading phase, and not actual simulation. Useful to validate 'input'.
    -b, --use-nonblocking,   Use non-blocking MPI communication
    -n, --name,              Name of the problem, used for output
    -s, --suppress-pinned,   Suppress usage of pinned memory for MPI communication buffers
    -o, --output,            Directory to put the output files
    -t, --timers,            String specifying the type of timer output
    --trace-data-migration,  Trace host-device data migration
    -m, --memory-usage,      Minimum threshold for printing out memory allocations in a member of the data repository.
    --pause-for,             Pause geosx for a given number of seconds before starting execution

    Rank 0: No XML input file nor schema specified. Exiting...

Obviously this doesn't do much interesting, but it will at least confirm that the executable runs.
In typical usage, an input XML must be provided describing the problem to be run, e.g.

``sh
    ./bin/geosx -i your-problem.xml


    (useful before running a heavy simulation).

In a parallel setting, the command might look something like

```sh
    mpirun -np 8 ./bin/geosx -i your-problem.xml -x 2 -y 2 -z 2

Note that we provide a series of :ref:`Tutorials` to walk you through the actual usage of the code, with several input examples.
Once you are comfortable the build is working properly, we suggest new users start working through these tutorials.

# Testing
It is wise to run our unit test suite as an additional check that everything is working properly.
You can run them in the build folder you just created.

```sh
  cd GEOS/build-your-platform-release
  ctest -V

This will run a large suite of simple tests that check various components of the code.
If you have access, you may also consider running the integrated tests.
Please refer to :ref:`IntegratedTests` for further information.


   Refer to the FAQs above for how best to proceed in this situation.
   If only a few tests fail, it is possible that your platform configuration has exposed some issue that our existing platform tests do not catch.
   If you suspect this is the case, please consider posting an issue to our issue tracker (after first checking whether other users have encountered a similar issue).
