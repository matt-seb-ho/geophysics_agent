**Context:** Developerguide > Contributing > IntegratedTests > ATS Configuration File

## ATS Configuration File
Files with the *.ats* extension are used to configure the integratedTests.
They use a Python 3.x syntax, and have a set of ATS-related methods loaded into the scope (TestCase, geos, source, etc.).
The root configuration file (*integratedTests/tests/allTests/main.ats*) finds and includes any test definitions in its subdirectories.
The remaining configuration files typically add one or more tests with varying partitioning and input xml files to ATS.

The *inputFiles/solidMechanics/sedov.ats* file shows how to add three groups of tests.
This file begins by defining a set of common parameters, which are used later:


  :language: python
  :start-after: # Integrated Test Docs Begin Parameters
  :end-before: # Integrated Test Docs End Parameters


It then enters over the requested partitioning schemes: 


  :language: python
  :start-after: # Integrated Test Docs Begin Test Loop
  :end-before: # Integrated Test Docs End Test Loop


and registers a unique test case with the `TestDeck` method, which accepts the following arguments:

* name : The name of the test
* description : A brief description of the test
* partitions : A list of partition schemes to be tested
* restart_step : The cycle number where GEOS should test its restart capability
* check_step : The cycle number where GEOS should evaluate output files
* restartcheck_params : Parameters to forward to the restart check (tolerance, etc.)
* curvecheck_params: Parameters to forward to the curve check (tolerance, etc.)



  For any given test step, we expect that at least one restart or curve check be defined.

