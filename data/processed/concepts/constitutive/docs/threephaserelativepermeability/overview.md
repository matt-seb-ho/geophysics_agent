**Context:** Constitutive > ThreePhaseRelativePermeability > Overview

# Overview
For the simulation of three-phase flow in porous media, it is common to use a specific treatment
(i.e., different from the typical two-phase procedure) to evaluate the oil relative permeability.
Specifically, the three-phase oil relative permeability is obtained by interpolation of oil-water
and oil-gas experimental data measured independently in two-phase displacements.

Let :math:[k_{rw,wo}` and :math:`k_{ro,wo}` be the water-oil two-phase relative permeabilities for the
water phase and the oil phase, respectively. Let :math:`k_{rg,go}` and :math:`k_{ro,go}` be the oil-gas
two-phase relative permeabilities for the gas phase and the oil phase, respectively.
In the current implementation, the two-phase relative permeability data is computed analytically using the :doc:`/coreComponents/constitutive/docs/BrooksCoreyRelativePermeability`.

The water and gas three-phase relative permeabilities are simply given by two-phase data and
only depend on :math:`S_w` and :math:`S_g`, respectively. That is,





The oil three-phase relative permeability
is obtained using a variant of the saturation-weighted interpolation procedure initially proposed
by `Baker ](http://dx.doi.org/10.2118/17369-MS)_. Specifically, we compute:



This procedure provides a simple but effective formula avoiding
the problems associated with the other interpolation methods (negative values).

Another option can be triggered using `threePhaseInterpolator` to set interpolation model to be STONEII described by:



...
