**Context:** Physicssolvers > Solidmechanics > SolidMechanics > Governing Equations

## Governing Equations
The `SolidMechanicsLagrangianFEM` solves the equations of motion as given by



which is a 3-dimensional expression for the well known expression of Newtons Second Law (:math:`F = m a`).
These equations of motion are discretized using the Finite Element Method,
which leads to a discrete set of residual equations:


