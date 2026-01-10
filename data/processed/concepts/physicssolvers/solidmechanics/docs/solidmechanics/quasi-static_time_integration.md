**Context:** Physicssolvers > Solidmechanics > SolidMechanics > Quasi-Static Time Integration

## Quasi-Static Time Integration
The Quasi-Static time integration option solves the equation of motion after removing the inertial term, which is expressed by



which is essentially a way to express the equation for static equilibrium (:math:`\Sigma F=0`).
Thus, selection of the Quasi-Static option will yield a solution where the sum of all forces at a given node is equal to zero.
The resulting finite element discretized set of residual equations are expressed as



Taking the derivative of these residual equations wrt. the primary variable (displacement) yields


            - \int\limits_{\Omega^e} \Phi_{a,k} \frac{\partial T_{ik}}{\partial u_{bj}}   dV,

And finally, the expression for the residual equation and derivative are used to express a non-linear system of equations


   \left( \left. \left({u}_{bj} \right) \right|^{n+1}_{{kiter}+1} - \left. \left({u}_{bj} \right) \right|^{n+1}_{kiter} \right)
   = - (R_{solid})_{ai}|^{n+1}_{kiter} ,

which are solved via the solver package.
