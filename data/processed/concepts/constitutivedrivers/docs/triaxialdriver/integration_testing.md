**Context:** Constitutivedrivers > TriaxialDriver > Integration Testing

## Integration Testing
The development team also uses the Triaxial Driver to perform unit testing on the various material models within GEOS.  The optional argument `baseline` can be used to point to a previous output file that has been validated  (e.g. against analytical or experimental benchmarks).  If such a file is specified, the driver will perform a loading run and then compare the new results against the baseline.  In this way, any regressions in the material models can be quickly identified.

Developers of new models are encouraged to add their own baselines to `src/coreComponents/constitutive/integrationTests`. Adding additional tests is straightforward:

1. Create a new xml file for your test in `src/coreComponents/constitutive/integrationTests`.  There are several examples is this directory already to use as a template.  We suggest using the naming convention `testTriaxial_myTest.xml`, so that all triaxial tests will be grouped together alphabetically.  Set the `output` file to `testTriaxial_myTest.txt`, and run your test.  Validate the results however is appropriate.

2. This output file will now become your new baseline.  Replace the `output` key with `baseline` so that the driver can read in your file as a baseline for comparison.  Make sure there is no remaining `output` key, or set `output=none`, to suppress further file output.  While you can certainly write a new output for debugging purposes, during our automated unit tests we prefer to suppress file output.  Re-run the triaxial driver to confirm that the comparison test passes.

3. Modify `src/coreComponents/constitutive/integrationTests/CMakeLists.txt` to enable your new test in the unit test suite.  In particular, you will need to add your new XML file to the existing list in the `gtest_triaxial_xmls` variable:



  set( gtest_triaxial_xmls
       testTriaxial_elasticIsotropic.xml
       testTriaxial_druckerPragerExtended.xml
       testTriaxial_myTest.xml
     )

4. Run `make` in your build directory to make sure the CMake syntax is correct

5. Run `ctest -V -R Triax` to run the triaxial unit tests.  Confirm your test is included and passes properly.

If you run into troubles, do not hesitate to contact the development team for help.
