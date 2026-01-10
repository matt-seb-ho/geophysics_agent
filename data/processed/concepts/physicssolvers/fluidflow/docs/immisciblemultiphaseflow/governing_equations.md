**Context:** Physicssolvers > Fluidflow > ImmiscibleMultiphaseFlow > Governing Equations

## Governing Equations
### Mass Conservation Equations
We consider a two-component system, say gas and water, flow in a compressible porous medium, in which both components can exist only in their corresponding phases of vapor and liquid. The gas and water components are denoted by the subscripts :math:`g` and
:math:`w`, respectively. Moreover, the liquid, which is the wetting phase, and the vapor, the non-wetting phase, are denoted by the subscripts :math:`\ell` and
:math:`v`, respectively. The mass conservation laws are expressed as:


  \rho_v q_v,

and


  \boldsymbol{u}_\ell) = \rho_\ell q_\ell,



where :math:`\phi(\mathbf{x})` is the porosity of the medium which is a function of pressure,
:math:`S_\ell(\mathbf{x},t)` is the saturation of the phase
:math:`\ell` and similarly for the phase :math:`v`, and :math:`t` is the time. The source/sink terms :math:`q_{\ell}` and :math:`q_{v}` are
positive for injection and negative for production. The phase
velocity, :math:`\boldsymbol{u}_\ell` and :math:`\boldsymbol{u}_v`, are defined using
the multiphase extension of Darcy's law (conservation of momentum) as

 

and

 

Here, :math:`k(\mathbf{x})` is the scalar absolute permeability of the medium, :math:`\lambda_\ell` is the phase mobility of the liquid phase defined as :math:`k_{r\ell}/\mu_\ell`, where :math:`k_{r\ell}(\mathbf{x},S_\ell)` is the phase relative permeability, :math:`\mu_\ell` is the phase viscosity, and :math:`\rho_{\ell}` is the phase density. 
These are also defined similarly for the vapor phase. In both cases we assume that the relative permeabilities are strictly increasing functions of their own saturation.
The gravitational acceleration is denoted by :math:`g`, and the
depth by :math:`z` (positive going downward).
The conservation of mass equations are constrained by the volume contraint equation:



Moreover, the capillary pressure constraint relates the two phase pressures with



We assume that capillary pressure is a strictly decreasing function of the wetting-phase saturation.

The evaluation of the relative permeabilities, capillary pressures, and
viscosities is reviewed in the section about :doc:`/coreComponents/constitutive/docs/Constitutive`.

We note that the formulation currently implemented in GEOS is isothermal. 

To summarize, the Immiscible multiphase flow solver assembles a set of :math:`n_p+1`
equations in each element, i.e., :math:`n_p` mass conservation equations and one volume constraint equation.

==================== ===========================
Number of equations  Equation type
==================== ===========================
:math:`n_p`          Mass conservation equations
1                    Volume constraint
==================== ===========================

.. _immiscible_primary_variables:
