**Context:** Tutorials > Step01 > Tutorial > Numerical methods

## Numerical methods
GEOS comes with several useful numerical methods.
In the `Solvers` elements, for instance, we had specified to use a two-point flux approximation
as discretization scheme for the finite volume single-phase solver.
Now to use this scheme, we need to supply more details in the `NumericalMethods` element.


  :language: xml
  :start-after: <!-- SPHINX_TUT_INT_HEX_NUM_METHODS -->
  :end-before: <!-- SPHINX_TUT_INT_HEX_NUM_METHODS_END -->

Note that in GEOS, there is a difference between physics solvers and numerical methods.
Their parameterizations are thus independent. We can have
multiple solvers using the same numerical scheme but with different tolerances, for instance.

The available numerical methods and their options are listed in the GEOS XML schema documentation which may be found by using the search function in the documentation.

.. _ElementRegions_tag_single_phase_internal_mesh:

--------