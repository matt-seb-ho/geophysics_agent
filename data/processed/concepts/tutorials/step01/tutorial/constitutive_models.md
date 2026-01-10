**Context:** Tutorials > Step01 > Tutorial > Constitutive models

## Constitutive models
The `Constitutive` element attaches physical properties to all materials contained in the domain.

The physical properties of the materials
defined as `water`, `rockPorosity`,  and `rockPerm` are provided here,
each material being derived from a different material type:
`CompressibleSinglePhaseFluid`
for the water, `PressurePorosity` for the rock porosity, and
`ConstantPermeability` for rock permeability.
The list of attributes differs between these constitutive materials.



  :language: xml
  :start-after: <!-- SPHINX_TUT_INT_HEX_CONSTITUTIVE -->
  :end-before: <!-- SPHINX_TUT_INT_HEX_CONSTITUTIVE_END -->


The names `water`, `rockPorosity` and `rockPerm` are defined by the user
as handles to specific instances of physical materials.
GEOS uses S.I. units throughout, not field units.
Pressures, for instance, are in Pascal, not psia.
The x- and y-permeability are set to 1.0e-12 m\ :sup:`2` corresponding to approximately to 1 Darcy.


We have used the handles `water`, `rockPorosity` and `rockPerm` in the input file
in the `ElementRegions` section of the XML file,
before the registration of these materials took place here, in Constitutive element.


  the order in which objects are registered and used in the XML file is not important.




.. _FieldSpecifications_tag_single_phase_internal_mesh:

--------------------