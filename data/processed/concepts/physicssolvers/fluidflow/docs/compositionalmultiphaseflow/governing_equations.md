**Context:** Physicssolvers > Fluidflow > CompositionalMultiphaseFlow > Governing Equations

## Governing Equations
### Mass Conservation Equations
Mass conservation for component :math:`c` is expressed as:


   + \nabla \cdot \bigg( \sum_\ell \rho_{\ell} \, y_{c \ell} \, \boldsymbol{u}_{\ell} \bigg)
   - \sum_\ell \rho_{\ell} \, y_{c \ell} \, q_{\ell} = 0,


where :math:`\phi` is the porosity of the medium,
:math:`S_{\ell}` is the saturation of phase :math:`\ell`, :math:`y_{c \ell}`
is the mass fraction of component :math:`c` in phase :math:`\ell`,
:math:`\rho_{\ell}` is the phase density, and :math:`t` is time. We note that the
formulation currently implemented in GEOS is isothermal.

### Darcy's Law
Using the multiphase extension of Darcy's law, the phase velocity :math:`\boldsymbol{u}_{\ell}`
is written as a function of the phase potential gradient :math:`\nabla \Phi_{\ell}`:


  = - \boldsymbol{k} \lambda_{\ell} \big( \nabla (p - P_{c,\ell}) - \rho_{\ell} g \nabla z \big).

In this equation, :math:`\boldsymbol{k}` is the rock permeability,
:math:`\lambda_{\ell} = k_{r \ell} / \mu_{\ell}` is the phase mobility,
defined as the phase relative permeability divided by the phase viscosity,
:math:`p` is the reference pressure, :math:`P_{c,\ell}` is the the capillary
pressure,  :math:`g` is the gravitational acceleration, and :math:`z` is depth.
The evaluation of the relative permeabilities, capillary pressures, and
viscosities is reviewed in the section about :doc:`/coreComponents/constitutive/docs/Constitutive`.

Combining the mass conservation equations with Darcy's law yields a set of :math:`n_c`
equations written as:


   - \nabla \cdot \boldsymbol{k} \bigg( \sum_\ell \rho_{\ell} \, y_{c \ell} \, \lambda_{\ell} \nabla \Phi_{\ell}   \bigg)
   - \sum_\ell \rho_{\ell} \, y_{c \ell} \, q_{\ell} = 0.

### Constraints and Thermodynamic Equilibrium
The volume constraint equation states that the pore space is always completely filled by
the phases. The constraint can be expressed as:



The system is closed by the following thermodynamic equilibrium constraints:



where :math:`f_{c \ell}` is the fugacity of component :math:`c` in phase :math:`\ell`.
The flash calculations performed to enforce the thermodynamical equilibrium are reviewed
in the section about :doc:`/coreComponents/constitutive/docs/Constitutive`.

To summarize, the compositional multiphase flow solver assembles a set of :math:`n_c+1`
equations in each element, i.e., :math:`n_c` mass conservation equations and one volume constraint equation.
A separate module discussed in the :doc:`/coreComponents/constitutive/docs/Constitutive`
is responsible for the enforcement of the thermodynamic equilibrium at each nonlinear iteration.

==================== ===========================
Number of equations  Equation type
==================== ===========================
:math:`n_c`          Mass conservation equations
1                    Volume constraint
==================== ===========================

.. _primary_variables:
