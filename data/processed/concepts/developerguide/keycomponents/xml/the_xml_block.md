**Context:** Developerguide > Keycomponents > XML > The XML block

## The XML block
We are ready to use the relative permeability model in GEOS.
The corresponding XML block (child node of the "Constitutive" block) reads:

``XML
  <Constitutive>
    <BrooksCoreyBakerRelativePermeability name="relperm"
                                          phaseNames="{oil, gas, water}"
                                          phaseMinVolumeFraction="{0.05, 0.05, 0.05}"
                                          waterOilRelPermExponent="{2.5, 1.5}"
                                          waterOilRelPermMaxValue="{0.8, 0.9}"
                                          gasOilRelPermExponent="{3, 3}"
                                          gasOilRelPermMaxValue="{0.4, 0.9}"/>
  <Constitutive>

With this construct, we instruct the `ConstitutiveManager` class (whose `catalogName` is "Constitutive") to instantiate a subgroup of type `BrooksCoreyRelativePermeability``.
We also fill the data members of the values that we want to use for the simulation.
For a simulation with multiple regions, we could define multiple relative permeability models in the "Constitutive" XML block (yielding multiple relperm subgroups in GEOS), with a unique name attribute for each model.

*For more examples on how to contribute to GEOS, please read* :ref:`AddingNewSolver`


# Input Schema Generation
A schema file is a useful tool for validating input .xml files and constructing user-interfaces.  Rather than manually maintaining the schema during development, GEOS is designed to automatically generate one by traversing the documentation structure.

To generate the schema, run GEOS with the input, schema, and the (optional) schema_level arguments, i.e.: `geosx -i input.xml -s schema.xsd`.  There are two ways to limit the scope of the schema:

1. Setting the verbosity flag for an object in the documentation structure.  If the schema-level argument is used, then only objects (and their children) and attributes with `(verbosity < schema-level)` will be output.

2. By supplying a limited input xml file.  When GEOS builds its data structure, it will only include objects that are listed within the xml (or those that are explicitly appended when those objects are initialized).  The code will add all available *attributes* for these objects to the schema.

To take advantage of this design it is necessary to use the automatic xml parsing approach that relies upon the documentation node.  If values are read in manually, then the schema can not be used to validate xml those inputs.

Note: the lightweight xml parser that is used in GEOS cannot be used to validate inputs with the schema directly.  As such, it is necessary to use an external tool for validation, such as the geosx_tools python module.
