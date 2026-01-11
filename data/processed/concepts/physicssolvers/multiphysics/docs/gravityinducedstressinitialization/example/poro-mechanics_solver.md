**Context:** Physicssolvers > Multiphysics > Gravityinducedstressinitialization > Example > Poro-Mechanics Solver

## Poro-Mechanics Solver
For the initialization test, a hydrostatic pore pressure is imposed on the system. This is done using the Hydrostatic Equilibrium tag under Field Specifications. We then define a poro-mechanics solver called here poroSolve. 
This solid mechanics solver (see :ref:`SolidMechanicsLagrangianFEM`) called `lagSolve` is based on the Lagrangian finite element formulation. 
The problem is run as `QuasiStatic` without considering inertial effects. 
The computational domain is discretized by `FE1`, defined in the `NumericalMethods` section.
We use the `targetRegions` attribute to define the regions where the poromechanics solver is applied.
Since we only have one cellBlockName type called `Domain`, the poromechanics solver is applied to every element of the model. 
The flow solver for this problem (see :ref:`SinglePhaseFlow`) called `SinglePhaseFlow` is discretized by `fluidTPFA`, defined in the `NumericalMethods` section.


    :language: xml
    :start-after: <!-- SPHINX_POROMECHANICSSOLVER -->
    :end-before: <!-- SPHINX_POROMECHANICSSOLVER_END -->


    :language: xml
    :start-after: <!-- SPHINX_NUMERICAL -->
    :end-before: <!-- SPHINX_NUMERICAL_END -->


------------------------------