**Context:** Physicssolvers > Fluidflow > ImmiscibleMultiphaseFlow > Primary Variables

## Primary Variables
There are two formulations implemented in GEOS for the Immiscible multiphsae solver and both formulations are based on
:math:`n_p+1` primary variables, namely, one pressure, :math:`p`, and
:math:`n_p` phase volume fractions, :math:`S_{p}`.


=========================== ===========================
Number of primary variables Variable type
=========================== ===========================
1                           Pressure
:math:`n_p - 1`             Phase volume fractions
=========================== ===========================

The main formulation is the standard formulation which solves the individual components mass conservation equations. Also, another formulation based on the total mass flux is implemented which is useful for multiple purposes such as hybrid upwinding techniques and sequential finite volume methods. This latter formulation is explained next. 

### Flow and Transport Equations
To develop this formulation we use a flux approximation as required by the finite-volume numerical solution scheme.
Thus, we choose to construct this approximation in fractional flow form, and with this we will be able to show the coupling between the different physical processes. This formulation is obtained by decomposing the governing equations into a flow problem for both phases and a transport problem for one of the two phases. 
To obtain this decomposition,  we use a total-mass balance formulation by summing both components mass conversation equations and then using the mass constraint to result in the following elliptic PDE governing the temporal evolution of the pressure field:



where 



and we defined a total mass flux as 



Next, the highly nonlinear parabolic transport equation is obtained by using  this total mass flux to formally eliminate the pressure variable from the individual components mass conservation equations, yielding


  = 
 \rho_v q_v,

and

.. math```
 \frac{\partial}{\partial t}(\phi\rho_\ell S_\ell) + \nabla \cdot F_\ell
  =  
 \rho_\ell q_\ell,

where the flow flux for each phase is defined as


 F_{\ell} :=
 \frac{\rho_\ell \lambda_\ell}{\rho_\ell \lambda_\ell+\rho_v 
 \lambda_v}\boldsymbol{U}_T}   + 
 k \frac{\rho_\ell \lambda_\ell\rho_v \lambda_v}{\rho_\ell \lambda_\ell+\rho_v 
 \lambda_v}(\rho_\ell - \rho_v) 
 g\nabla z
 +
 k \frac{\rho_\ell \lambda_\ell\rho_v \lambda_v}{\rho_\ell \lambda_\ell+\rho_v 
 \lambda_v} ( \nabla P_{c})

and


 F_{v} :=
 \frac{\rho_v \lambda_v}{\rho_\ell \lambda_\ell+\rho_v 
 \lambda_v}\boldsymbol{U}_T}   + 
 k \frac{\rho_\ell \lambda_\ell\rho_v \lambda_v}{\rho_\ell \lambda_\ell+\rho_v 
 \lambda_v}(\rho_v - \rho_\ell) 
 g\nabla z
 -
 k \frac{\rho_\ell \lambda_\ell\rho_v \lambda_v}{\rho_\ell \lambda_\ell+\rho_v 
 \lambda_v} ( \nabla P_{c})




.. _immiscible_discretization:
