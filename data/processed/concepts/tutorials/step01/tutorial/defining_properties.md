**Context:** Tutorials > Step01 > Tutorial > Defining properties

## Defining properties
In the `FieldSpecifications` section, properties such as source and sink pressures are set.
GEOS offers a lot of flexibility to specify field values through space and time.

Spatially, in GEOS, all field specifications are associated
to a target object on which the field values are mounted.
This allows for a lot of freedom in defining fields:
for instance, one can have volume property values attached to
a subset of volume elements of the mesh,
or surface properties attached to faces of a subset of elements.

For each `FieldSpecification`, we specify a `name`, a `fieldName` (this name is used by solvers or numerical methods), an `objectPath`, `setNames` and a `scale`. The `ObjectPath` is important and it reflects the internal class hierarchy of the code.
Here, for the `fieldName` pressure, we assign the value defined by `scale` (5e6 Pascal)
to one of the `ElementRegions` (class) called `mainRegions` (instance).
More specifically, we target the `elementSubRegions` called `cellBlock`
(this contains all the C3D8 elements, effectively all the domain). The `setNames` allows to use the elements defined in `Geometry`, or use everything in the object path (using the `all`).



  :language: xml
  :start-after: <!-- SPHINX_TUT_INT_HEX_FIELDS -->
  :end-before: <!-- SPHINX_TUT_INT_HEX_FIELDS_END -->

The image below shows the pressures after the very first time step, with the domain initialized at 5 MPa, the sink at 0 MPa on the top right, and the source in the lower left corner at 10 MPa.







.. _Outputs_tag_single_phase_internal_mesh:

-------