**Context:** Fileio > Doc > InputXMLFiles > Validation

## Validation
Unmatched special characters ($, [, \`, etc.) in the final xml file indicate that parameters, units, or symbolic math were not specified correctly.  
If the prepreprocessor detects these, it will throw an error and exit.
Additional validation of the compiled files can be completed with `preprocess_xml` by supplying the -s argument and the path to the GEOS schema.

