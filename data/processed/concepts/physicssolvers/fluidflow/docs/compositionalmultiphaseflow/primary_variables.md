**Context:** Physicssolvers > Fluidflow > CompositionalMultiphaseFlow > Primary Variables

## Primary Variables
The variable formulation implemented in GEOS is a global variable formulation based on
:math:`n_c+1` primary variables, namely, one pressure, :math:`p`, and
:math:`n_c` component densities, :math:`\rho_c`.
By default, we use molar component densities.
A flag discussed in the section :ref:`parameters` can be used to select mass component densities instead of molar component densities.

=========================== ===========================
Number of primary variables Variable type
=========================== ===========================
1                           Pressure
:math:`n_c`                 Component densities
=========================== ===========================

Assembling the residual equations and calling the
:doc:`/coreComponents/constitutive/docs/Constitutive` requires computing the molar component
fractions and saturations. This is done with the relationship:



where



These secondary variables are used as input to the flash calculations.
After the flash calculations, the saturations are computed as:



where :math:`\nu_{\ell}` is the global mole fraction of phase :math:`\ell`
and :math:`\rho_{\ell}` is the molar density of phase :math:`\ell`.
These steps also involve computing the derivatives of the component
fractions and saturations with respect to the pressure and component densities.

.. _discretization:
