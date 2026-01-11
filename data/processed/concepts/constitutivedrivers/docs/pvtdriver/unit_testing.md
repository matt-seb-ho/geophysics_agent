**Context:** Constitutivedrivers > PVTDriver > Unit Testing

## Unit Testing
The development team also uses the PVTDriver to perform unit testing on the various fluid models within GEOS.  
The optional argument `baseline` can be used to point to a previous output file that has been validated  (e.g. against experimental benchmarks or reference codes).  
If such a file is specified, the driver will perform a testing run and then compare the new results against the baseline.  
In this way, any regressions in the fluid models can be quickly identified.

Developers of new models are encouraged to add their own baselines to `src/coreComponents/constitutive/unitTests`. 
Adding additional tests is straightforward:

1. Create a new xml file for your test in `src/coreComponents/constitutive/unitTests` or (easier) add extra blocks to the existing XML at `src/coreComponents/constitutive/unitTests/testPVT.xml`.  
For new XMLs, we suggest using the naming convention `testPVT_myTest.xml`, so that all tests will be grouped together alphabetically.  
Set the `output` file to `testPVT_myTest.txt`, and run your test.  
Validate the results however is appropriate.
If you have reference data available for this validation, we suggest archiving it in the `testPVT_data/` subdirectory, with a description of the source and formatting in the file header.
Several reference datasets are included already as examples.
This directory is also a convenient place to store auxiliary input files like PVT tables.

2. This output file will now become your new baseline.  
Replace the `output` key with `baseline` so that the driver can read in your file as a baseline for comparison.  
Make sure there is no remaining `output` key, or set `output=none`, to suppress further file output.  
While you can certainly write a new output for debugging purposes, during our automated unit tests we prefer to suppress file output.  
Re-run the driver to confirm that the comparison test passes.

3. Modify `src/coreComponents/constitutive/unitTests/CMakeLists.txt` to enable your new test in the unit test suite.  
In particular, you will need to add your new XML file to the existing list in the `gtest_pvt_xmls` variable.  
Note that if you simply added your test to the existing `testPVT.xml` file, no changes are needed.



  set( gtest_pvt_xmls
       testPVT.xml
       testPVT_myTest.xml
     )

4. Run `make` in your build directory to make sure the CMake syntax is correct

5. Run `ctest -V -R PVT` to run the PVT unit tests.  Confirm your test is included and passes properly.

If you run into troubles, do not hesitate to contact the development team for help.
