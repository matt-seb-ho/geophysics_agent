**Context:** Developerguide > Contributing > IntegratedTests > Test Output

## Test Output
Output files from the tests will be stored in the specified working directory (linked here: */path/to/GEOS/build-xyz/integratedTests/TestsResults*).
Using the serial beam bending test as an example, key output files include:

* *beamBending_01.data* : Contains the standard output for all test steps.
* *beamBending_01.err* :  Contains the standard error output for all test steps.
* *displacement_history.hdf5* : Contains time history information that is used as an input to the curve check step.
* *totalDisplacement_trace.png* : A figure displaying the results of the curve check step.
* *beamBending.geos.out* : Contains the standard output for only the geos run step.
* *beamBending_restart_000000010.restartcheck* which holds all of the standard output for only the *restartcheck* step.
* *beamBending_restart_000000010.0.diff.hdf5* which mimmics the hierarchy of the restart file and has links to the 

See :ref:`Restart Check <restart-check>` and :ref:`Curve Check <curve-check>` for further details on the test checks and output files.


.. _restart-check:

# Restart Check
This check compares a restart file output at the end of a run against a baseline. 
The python script that evaluates the diff is included in the `geos_ats` package, and is located here: *integratedTests/scripts/geos_ats_package/geos_ats/helpers/restart_check.py*.
The script compares the two restart files and writes out a *.restart_check* file with the results, as well as exiting with an error code if the files compare differently.
This script takes two positional arguments and a number of optional keyword arguments:

* file_pattern : Regex specifying the restart file. If the regex matches multiple files the one with the greater string is selected. For example *restart_100.hdf5* wins out over *restart_088.hdf5*.
* baseline_pattern : Regex specifying the baseline file.
* -r/--relative : The relative tolerance for floating point comparison, the default is 0.0.
* -a/--absolute : The absolute tolerance for floating point comparison, the default is 0.0.
* -e/--exclude : A list of regex expressions that match paths in the restart file tree to exclude from comparison. The default is [.*/commandLine].
* -w/-Werror : Force warnings to be treated as errors, default is false.
* -m/--skip-missing : Ignore values that are missing from either the baseline or target file.

The  itself starts off with a summary of the arguments.
The script begins by recording the arguments to the *.restart_check* file header, and then compares the *.root* restart files to their baseline.
If these match, the script will compare the linked *.hdf5* data files to their baseline.
If the script encounters any differences it will output an error message, and record a summary to the *.restart_check* file.

The restart check step can be run in parallel using mpi via

``sh
  mpirun -n NUM_PROCESSES python -m mpi4py restartcheck.py ...

In this case rank zero reads in the restart root file and then each rank parses a subset of the data files creating a *.$RANK.restartcheck* file. Rank zero then merges the output from each of these files into the main *.restartcheck* file and prints it to standard output.

