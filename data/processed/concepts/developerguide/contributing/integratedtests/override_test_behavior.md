**Context:** Developerguide > Contributing > IntegratedTests > Override Test Behavior

## Override Test Behavior
For cases where you need additional control over the integrated tests behavior, you can use this script in your build directory: */path/to/GEOS/build-xyz/integratedTests/geos_ats.sh*.
To run the tests, simply call this script with any desired arguments (see the output of `geos_ats.sh --help` for additional details.)
Common options for this script include:

* -a/--action : The type of action to run.  Common options include: `run`, `veryclean`, `rebaseline`, and `rebaselinefailed`.
* -r/--restartCheckOverrides : Arguments to pass to the restart check function.  Common options include: `skip_missing` (ignores any new/missing values in restart files) and `exclude parameter1 parameter2` (ignore these values in restart files).
* --machine : Set the ats machine type name.
* --ats : Pass an argument to the underlying ats framework.  Running `geos_ats.sh --ats help` will show you a list of available options for your current machine.

