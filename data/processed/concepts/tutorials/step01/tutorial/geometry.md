**Context:** Tutorials > Step01 > Tutorial > Geometry

## Geometry
The `Geometry` tag allows users to capture subregions of a mesh and assign them a unique name.
Here, we name two `Box` elements, one for the location of the `source` and one for the `sink`.
Pressure values are assigned to these named regions elsewhere in the input file.

The pressure source is the element in the (0,0,0) corner of the domain, and the sink is the element in the (10,10,10) corner.

For an element to be inside a geometric region,
it must have all its vertices strictly inside that region.
Consequently, we need to extend the geometry limits a small amount beyond the actual coordinates of the elements to catch all vertices. Here, we use a safety padding of 0.01.


  :language: xml
  :start-after: <!-- SPHINX_TUT_INT_HEX_GEOMETRY -->
  :end-before: <!-- SPHINX_TUT_INT_HEX_GEOMETRY_END -->

There are several methods to achieve similar conditions (Dirichlet boundary condition on faces, etc.).
The `Box` defined here is one of the simplest approaches.






.. _Events_tag_single_phase_internal_mesh:

--------