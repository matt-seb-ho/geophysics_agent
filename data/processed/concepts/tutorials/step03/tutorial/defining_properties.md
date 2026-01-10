**Context:** Tutorials > Step03 > Tutorial > Defining properties

## Defining properties
The next step is to specify fields, including:

  - The initial value (here, the pressure has to be initialized)
  - The static properties (here, we have to define the permeability tensor and the porosity)
  - The boundary conditions (here, the injection and production pressure have to be set)


  :language: xml
  :start-after: <!-- SPHINX_FIELD_CASE_FIELD -->
  :end-before: <!-- SPHINX_FIELD_CASE_FIELD_END -->

You may note :

 - All static parameters and initial value fields must have `initialCondition` field set to `1`.
 - The `objectPath` refers to the `ElementRegion` in which the field has its value,
 - The `setName` field points to the box previously defined to apply the fields,
 - `name` and `fieldName` have a different meaning: `name` is used to give a name to the XML block. This `name` must be unique. `fieldName` is the name of the field registered in GEOS. This value has to be set according to the expected input fields of each solver.

.. _Outputs_tag_field_case:

-------