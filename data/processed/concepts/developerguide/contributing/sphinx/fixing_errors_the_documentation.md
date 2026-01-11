**Context:** Developerguide > Contributing > Sphinx > Fixing errors the documentation

# Fixing errors the documentation
As part of the Continuous Integration process, the documentation is built on readthedocs, and any warnings or errors result in a failure test failure. 
What follows is a brief guide on how to fix the most common errors.

#. Navigate to the readthedocs build logs. This can be done by clicking on the failed test in the github test summary.


   :width: 600

#. Download the logs from the failed test on readthedocs through the "view raw" button.


   :width: 600

#. Perform a case sensitive search for "WARNING:" or "ERROR" to locate the sphinx issues. 
Note that there will be numerous doxygen warnings that should be ignored.