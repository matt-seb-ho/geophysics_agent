**Context:** Tutorials > Step03 > Tutorial > Single-phase solver

## Single-phase solver
Let us inspect the **Solver** XML tags.


  :language: xml
  :start-after: <!-- SPHINX_FIELD_CASE_SOLVER -->
  :end-before: <!-- SPHINX_FIELD_CASE_SOLVER_END -->


This node gathers all the information previously defined.
We use a classical `SinglePhaseFVM` Finite Volume Method,
with the two-point flux approximation
as will be defined in the **NumericalMethods** tag.
The `targetRegions` refers only
to the Reservoir region because we only solve for flow in this region.


The `NonlinearSolverParameters` and `LinearSolverParameters` are used to set usual
numerical solver parameters such as the linear and nonlinear tolerances, the preconditioner and solver types or the maximum number of nonlinear iterations.


.. _Mesh_tag_field_case:

-------