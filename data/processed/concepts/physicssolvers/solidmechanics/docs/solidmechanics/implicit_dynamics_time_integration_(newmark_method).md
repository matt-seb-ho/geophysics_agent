**Context:** Physicssolvers > Solidmechanics > SolidMechanics > Implicit Dynamics Time Integration (Newmark Method)

## Implicit Dynamics Time Integration (Newmark Method)
For implicit dynamic time integration, we use an implementation of the classical Newmark method.
This update method can be posed in terms of a simple SDOF spring/dashpot/mass model.
In the following, :math:`M` represents the mass, :math:`C` represent the damping of the dashpot, :math:`K`
represents the spring stiffness, and :math:`F` represents some external load.



and a series of update equations for the velocity and displacement at a point:


   u^{n+1} &= u^n + \left( v^{n} + \inv{2} \left[ (1-2\beta) a^n + 2\beta a^{n+1} \right] \Delta t \right) \Delta t, \\
   v^{n+1} &= v^n + \left[(1-\gamma) a^n + \gamma a^{n+1} \right] \Delta t.

As intermediate quantities we can form an estimate (predictor) for the end of step displacement and midstep velocity by
assuming zero end-of-step acceleration.


   \tilde{v}^{n+1} &= v^n + (1-\gamma) a^n  \Delta t =  v^n + \hat{\tilde{v}}

This gives the end of step displacement and velocity in terms of the predictor with a correction for the end
step acceleration.


   v^{n+1} &= \tilde{v}^{n+1} + \gamma a^{n+1} \Delta t

The acceleration and velocity may now be expressed in terms of displacement, and ultimately in terms
of the incremental displacement.


   v^{n+1} &= \tilde{v}^{n+1} + \frac{\gamma}{\beta \Delta t} \left(u^{n+1} - \tilde{u}^{n+1} \right) = \tilde{v}^{n+1} + \frac{\gamma}{\beta \Delta t} \left(\hat{u} - \hat{\tilde{u}} \right)

plugging these into equation of motion for the SDOF system gives:



Finally, we assume Rayliegh damping for the dashpot.



Of course we know that we intend to model a system of equations with many DOF.
Thus the representation for the mass, spring and dashpot can be replaced by our finite element discretized
equation of motion.
We may express the system in context of a nonlinear residual problem


        \int\limits_{\Gamma_t^e} \Phi_a t_i   dA  \\
        &- \int\limits_{\Omega^e} \Phi_{a,j} \left(T_{ij}^{n+1}+  a_{stiff} \left(\pderiv{T_{ij}^{n+1}}{\hat{u}_{bk}} \right)_{elastic} \left( \tilde{v}_{bk}^{n+1} + \frac{\gamma}{\beta \Delta t} \left(\hat{u}_{bk} - \hat{\tilde{u}}_{bk} \right) \right) \right)  dV \notag \\
        &+\int\limits_{\Omega^e} \Phi_a \rho \left(b_{i}- \Phi_b  \left( a_{mass} \left( \tilde{v}_{bi}^{n+1} + \frac{\gamma}{\beta \Delta t} \left(\hat{u}_{bi} - \hat{\tilde{u}}_{bi} \right) \right) + \frac{1}{\beta \Delta t^2}  \left( \hat{u}_{bi} - \hat{\tilde{u}}_{bi} \right) \right) \right)  dV ,\notag \\
    \pderiv{(R_{solid}^e)_{ai}}{\hat{u}_{bj}} &=
        - \int\limits_{\Omega^e} \Phi_{a,k} \left(\pderiv{T_{ik}^{n+1}}{\hat{u}_{bj}}+  a_{stiff} \frac{\gamma}{\beta \Delta t} \left(\pderiv{T_{ik}^{n+1}}{\hat{u}_{bj}} \right)_{elastic} \right)   dV \notag \\
        &- \left( \frac{\gamma a_{mass}}{\beta \Delta t} + \frac{1}{\beta \Delta t^2}  \right) \int\limits_{\Omega^e} \rho \Phi_a \Phi_c    \pderiv{ \hat{u}_{ci} }{\hat{u}_{bj}}dV .

Again, the expression for the residual equation and derivative are used to express a non-linear system of equations


   \left( \left. \left({u}_{bj} \right) \right|^{n+1}_{{kiter}+1} - \left. \left({u}_{bj} \right) \right|^{n+1}_{kiter} \right)
   = - (R_{solid})_{ai}|^{n+1}_{kiter} ,

which are solved via the solver package. Note that the derivatives involving :math:`u` and :math:`\hat{u}` are interchangable,
as are differences between the non-linear iterations.
