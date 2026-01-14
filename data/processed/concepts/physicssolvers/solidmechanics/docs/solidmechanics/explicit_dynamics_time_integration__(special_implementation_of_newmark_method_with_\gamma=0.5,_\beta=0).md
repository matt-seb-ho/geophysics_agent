**Context:** Physicssolvers > Solidmechanics > SolidMechanics > Explicit Dynamics Time Integration  (Special Implementation of Newmark Method with \gamma=0.5, \beta=0)

## Explicit Dynamics Time Integration  (Special Implementation of Newmark Method with \gamma=0.5, \beta=0)
For the Newmark Method, if \gamma=0.5, \beta=0, and the inertial term contains a diagonalized "mass matrix",
the update equations may be carried out without the solution of a system of equations.
In this case, the update equations simplify to a non-iterative update algorithm.

First the mid-step velocity and end-of-step displacements are calculated through the update equations


   \tensor{u}^{n+1} &= \tensor{u}^n + \tensor{v}^{n+1/2} \Delta t.

Then the residual equation/s are calculated, and acceleration at the end-of-step is calculated via



Note that the mass matrix must be diagonal, and damping term may not include the stiffness based damping
coefficient for this method, otherwise the above equation will require a system solve.
Finally, the end-of-step velocities are calculated from the end of step acceleration:



Note that the velocities may be stored at the midstep, resulting one less kinematic update.
This approach is typically referred to as the "Leapfrog" method.
However, in GEOS we do not offer this option since it can cause some confusion that results from the
storage of state at different points in time.


# Parameters
In the preceding XML block, The `SolidMechanicsLagrangianFEM` is specified by the title of the subblock of the `Solvers` block.
The following attributes are supported in the input block for `SolidMechanicsLagrangianFEM`:



The following data are allocated and used by the solver:



# Example
An example of a valid XML block is given here:


  :language: xml
  :start-after: <!-- SPHINX_SOLID_MECHANICS_SOLVER -->
  :end-before: <!-- SPHINX_SOLID_MECHANICS_SOLVER_END -->
