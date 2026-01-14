**Context:** Developerguide > Contributing > IntegratedTests > Test Filtering

## Test Filtering
An arbitrary number of filter arguments can be supplied to ATS to limit the number of tests to be run.
Filter arguments should refer to an ATS test variable and use a python-syntax (e.g.: "'some_string' in ats_variable" or "ats_variable<10").
These can be set via command-line arguments (possible via the `ATS_ARGUMENTS` variable):

```sh
  ./geos_ats.sh --ats f "np==1" --ats f "'SinglePhaseFVM' in solvers"


or via an environment variable (`ATS_FILTER`):

```sh
  export ATS_FILTER="np==1,'SinglePhaseFVM' in solvers"


Common ATS variables that you can filter tests include:

* np : The number of parallel processes for the test
* label : The name of the test case (e.g.: "sedov_01")
* collection : The name of the parent test folder (e.g.: "contactMechanics")
* checks : A comma-separated list of checks (e.g.: "curve,restart")
* solvers : A comma-separated list of solver types (e.g.: "SinglePhaseFVM,SurfaceGenerator")
* outputs : A comma-separated list of output types (e.g.: "Restart,VTK")
* constitutive_models : A comma-separated list of constitutive model types (e.g.: "CompressibleSinglePhaseFluid,ElasticIsotropic")


# Inspecting Test Results
While the tests are running, the name and size of the active test will be periodically printed out to the screen.
Test result summaries will also be periodically written to the screen and files in */path/to/GEOS/build-xyz/integratedTests/TestsResults*.
For most users, we recommend inspecting the *test_results.html* file in your browser (e.g.: `firefox integratedTests/TestsResults/test_results.html`).
Tests will be organized by their status variable, which includes:


* *RUNNING* : The test is currently running
* *NOT RUN* : The test is waiting to start
* *PASSED* : The test and associated checks succeeded
* *FAIL RUN* : The test was unable to run (this often occurs when there is an error in the .ats file)
* *FAIL CHECK* : The test ran to completion, but failed either its restart or curve check
* *SKIPPED* : The test was skipped (likely due to lack of computational resources)


If each test ends up in the *PASSED* category, then you are likely done with the integrated testing procedure.
However, if tests end up in any other category, it is your responsibility to address the failure.
If you identify that a failure is due to an expected change in the code (e.g.: adding a new parameter to the xml structure or fixing a bug in an algorithm), you can follow the :ref:`rebaselining procedure <rebaselining-tests>`.
Otherwise, you will need to track down and potentially fix the issue that triggered the failure.

