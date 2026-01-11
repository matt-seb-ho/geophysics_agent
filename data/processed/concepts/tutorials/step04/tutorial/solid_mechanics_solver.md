**Context:** Tutorials > Step04 > Tutorial > Solid mechanics solver

## Solid mechanics solver
The solid mechanics solver is based on the small strain Lagrangian finite element formulation.
The problem is run as `QuasiStatic` without considering the beam inertial. The computational
domain is discretized by `FE1`,
which is defined in the `NumericalMethods` block. The material is designated as
`shale`, whose properties are defined in the
`Constitutive` block.


  :language: xml
  :start-after: <!-- SPHINX_SolidMechanicsSolver -->
  :end-before:  <!-- SPHINX_SolidMechanicsSolverEnd -->

------------------------------------