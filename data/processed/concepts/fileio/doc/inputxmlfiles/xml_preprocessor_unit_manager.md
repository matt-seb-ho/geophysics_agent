**Context:** Fileio > Doc > InputXMLFiles > XML Preprocessor Unit Manager

## XML Preprocessor Unit Manager
Users wishing to work with non-SI units for specific values can define these explicitly via XML parameters postfixes.
The XML preprocessor ensures that any user-specified units within input files are converted into GEOS supported values prior to simulation.

The user can specify units by appending a valid value with a unit definition in square braces.

The unit manager supports most common units and SI prefixes, using both long- and abbreviated names (e.g.: c, centi, k, kilo, etc.).
Units may include predefined composite units (dyne, N, etc.) or may be built up from sub-units using a python syntax (e.g.: [N], [kg*m/s**2]).
Any (or no) amount of whitespace is allowed between the number and the unit bracket.
Here is a set of parameters with units specified:

```xml
  <Parameters>
    <Parameter name="parameter_a" value="2[m]"/>
    <Parameter name="parameter_b" value="1.2 [cm]"/>
    <Parameter name="parameter_c" value="1.23e4 [bbl/day]"/>
    <Parameter name="parameter_d" value="1.23E-4 [km**2]"/>
  </Parameters>


Please note that the preprocessor currently does not check whether any user-specified units are appropriate for a given input or symbolic expression.
