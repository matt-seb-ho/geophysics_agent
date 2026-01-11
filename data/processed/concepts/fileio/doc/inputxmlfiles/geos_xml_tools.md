**Context:** Fileio > Doc > InputXMLFiles > GEOS XML Tools

## GEOS XML Tools
The geosx_xml_tools package, which is used to enable advanced features such as parameters, symbolic math, etc., contains tools for validating xml files.
To do so, call the command-line script with the -s argument, i.e.: `preprocess_xml input_file.xml -s /path/to/schema.xsd`.
After compiling the final xml file, pygeosx will fetch the designated schema, validate, and print any errors to the screen.

Note: Attributes that are using advanced xml features will likely contain characters that are not allowed by their corresponding type pattern.
As such, file editors that are configured to use other validation methods will likely identify errors in the raw input file.


# XML Schema
An XML schema definition (XSD) file lays out the expected structure of an input XML file.
During the build process, GEOS automatically constructs a comprehensive schema from the code's data structure, and updates the version in the source (GEOS/src/coreComponents/schema/schema.xsd).

