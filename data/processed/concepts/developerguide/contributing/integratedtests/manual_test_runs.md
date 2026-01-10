**Context:** Developerguide > Contributing > IntegratedTests > Manual Test Runs

## Manual Test Runs
Before running the integrated tests manually, we recommend that you define the following variables in your machine's host configuration file:

* `ATS_WORKING_DIR` : The location where tests should be run (default=*GEOS/[build-dir]/integratedTests/workingDir*)
* `ATS_BASELINE_DIR` : The location where test baselines should be stored (default=*GEOS/integratedTests*)




After building GEOS, the integrated tests can be triggered in the GEOS build directory with the following commands:

* `make ats_environment` : Setup the testing environment (Note: this step is run by default for the other make targets).  This process will install packages required for testing into the python environment defined in your current host config file.  Depending on how you have built GEOS, you may be prompted to manually run the `make pygeosx` command and then re-run this step.
* `make ats_run` : Run all of the available tests (see the below note on testing resources).
* `make ats_clean` : Remove any unnecessary files created during the testing process (.vtk, .hdf5 files, etc.)
* `make ats_rebaseline` : Selectively update the baseline files for tests.
* `make ats_rebaseline_failed` : Automatically update the baseline files for any failed tests.






  If you are on a shared system, we recommend that you only run `make ats_run` within an allocation.



  For example, on LLNL Lassen builds we select a couple of runtime options:
  set(ATS_ARGUMENTS "--ats jsrun_omp --ats jsrun_bind=packed"  CACHE STRING "")





.. _overrideTestBehavior:
