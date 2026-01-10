**Context:** Tutorials > Step01 > Tutorial > Regions

## Regions
In GEOS, `ElementsRegions` are used to attach material properties
to regions of elements.
Here, we use only one **CellElementRegion** to represent the entire domain (user name: `mainRegion`).
It contains all the blocks called `cellBlock` defined in the mesh section.
We specify the materials contained in that region using a `materialList`.
Several materials coexist in `cellBlock`, and we list them using their user-defined names: 
`water` and `rock` in this exemple.
Each material is a definition of physical properties.



  :language: xml
  :start-after: <!-- SPHINX_TUT_INT_HEX_ELEM_REGIONS -->
  :end-before: <!-- SPHINX_TUT_INT_HEX_ELEM_REGIONS_END -->



.. _Constitutive_tag_single_phase_internal_mesh:

---------------------