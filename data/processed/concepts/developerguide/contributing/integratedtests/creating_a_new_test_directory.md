**Context:** Developerguide > Contributing > IntegratedTests > Creating a New Test Directory

## Creating a New Test Directory
To add a new set of tests, create a new folder under the `GEOS/inputFiles` directory.
This folder needs to include at least one *.ats* file to be included in the integrated tests.
Using the sedov example, after creating *sedov.ats* the directory should look like

```sh
  - inputFiles/solidMechanics
    - sedov.ats
    - sedov.xml


These changes will be reflected in the new baselines after triggering the manual rebaseline step. 


.. _rebaselining-tests:

# Rebaselining Tests
Occasionally you may need to add or update baseline files in the repository (possibly due to feature changes in the code).
This process is called rebaselining.
We suggest the following workflow:


#. Open a pull request for your branch on github and select the **ci: run integrated tests** label
#. Wait for the tests to finish
#. Download and unpack the new baselines from the link provided at the bottom of the test logs
#. Inspect the test results using the *test_results.html* file
#. Verify that the changes in the baseline files are desired
#. Update the baseline ID in the *GEOS/.integrated_tests.yaml* file
#. Add a justification for the baseline changes to the *GEOS/BASELINE_NOTES.md* file
#. Commit your changes and push the code
#. Wait for the CI tests to re-run and verify that the integrated tests step passed




# Tips
**Parallel Tests**: On some development machines geosxats won't run parallel tests by default (e.g. on an linux laptop or workstation), and as a result many baselines will be skipped.
We highly recommend running tests and rebaselining on an MPI-aware platform.

**Filtering Checks**: A common reason for rebaselining is that you have changed the name of an XML node in the input files.
While the baselines may be numerically identical, the restarts will fail because they contain different node names.
In this situation, it can be useful to add a filter to the restart check script using the *geos_ats.sh* script (see the `-e` and `-m` options in :ref:`overrideTestBehavior` )
