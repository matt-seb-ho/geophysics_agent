**Context:** Tutorials > Step03 > Tutorial > Regions

## Regions
Assuming that the overburden and the underburden are impermeable,
and flow only takes place in the reservoir, we need to define regions.

We need to define all the `CellElementRegions` according to the `attribute` values of the VTK file
(which are respectively `1`, `2` and `3` for each region). As mentioned above, the solvers is only
applied on the reservoir layer, (on region `2`). In this case, the **ElementRegions** tag is :


  :language: xml
  :start-after: <!-- SPHINX_FIELD_CASE_REGION -->
  :end-before: <!-- SPHINX_FIELD_CASE_REGION_END -->



.. _Constitutive_tag_field_case:

--------------------