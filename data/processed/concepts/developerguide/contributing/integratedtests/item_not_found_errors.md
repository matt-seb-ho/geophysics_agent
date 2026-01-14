**Context:** Developerguide > Contributing > IntegratedTests > Item Not Found Errors

## Item Not Found Errors
The following error would indicate that the requested baseline file was not found:

``sh
  baseline file not found: /path/to/baseline/file


This type of error can occur if you are adding a new test, or if you time history output failed.



The following errors would indicate that values were not found in time history files:

``sh
  Value not found in target file: value
  Set not found in target file: setname
  Could not find location string for parameter: value, search...
  

The following error would indicate that a given curve exceeded its tolerance compared to script-generated values:


```sh
  script_value_setname diff exceeds tolerance: ||t-b||/N=100.0, script_tolerance=1.0



# Adding and Modifying Tests