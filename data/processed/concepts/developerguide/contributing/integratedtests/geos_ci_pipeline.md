**Context:** Developerguide > Contributing > IntegratedTests > GEOS CI Pipeline

## GEOS CI Pipeline
In most cases, developers will be able to rely on the integrated tests that are run as part of the GEOS CI Pipeline.
These can be triggered if the **ci: run integrated tests** label is selected for a pull request (this can be added from the right-hand panel on PR page).

To inspect the results of CI tests, select the *Checks* tab from the top of the pull request and then select *run_integrated_tests/build_test_deploy* from the left-hand panel.



   :width: 400px



   :width: 400px


This page will show the full output of GEOS build process and the integrated test suite.
At the bottom of this page, the logs will contain a summary of the test results and a list of any ignored/failed tests.


``sh
  =======================
  Integrated test results
  =======================
  expected: 0
  created: 0
  batched: 0
  filtered: 104
  skipped: 0
  running: 0
  passed: 215
  timedout: 0 (3 ignored)
  halted: 0
  lsferror: 0
  failed: 0
  =======================
  Ignored tests
  =======================
  pennyShapedToughnessDominated_smoke_01
  pennyShapedViscosityDominated_smoke_01
  pknViscosityDominated_smoke_01
  =======================
  Overall status: PASSED
  =======================


The log will provide instructions on where to download the test results and a baseline ID that can be assigned in the *.integrated_tests.yaml* file.



. code-block:: sh

  Download the bundle at https://storage.googleapis.com/geosx/integratedTests/baseline_integratedTests-pr3044-4400-e6359ca.tar.gz
  New baseline ID: baseline_integratedTests-pr3044-4400-e6359ca





