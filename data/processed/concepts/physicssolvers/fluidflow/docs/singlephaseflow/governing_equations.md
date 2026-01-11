**Context:** Physicssolvers > Fluidflow > SinglePhaseFlow > Governing Equations

## Governing Equations
This is a cell-centered Finite Volume solver for compressible single-phase flow in porous media.
Fluid pressure as the primary solution variable.
Darcy's law is used to calculate fluid velocity from pressure gradient.
The solver currently only supports Dirichlet-type boundary conditions (BC) applied on cells or faces and Neumann no-flow type BC.

The following mass balance equation is solved in the domain:



where



and :math:`\phi` is porosity, :math:`\rho` is fluid density, :math:`\mu` is fluid viscosity,
:math:`\boldsymbol{k}` is the permeability tensor, :math:`\boldsymbol{g}` is the gravity vector,
and :math:`q` is the source function (currently not supported). The details on the computation of the density and the viscosity are given in :ref:`CompressibleSinglePhaseFluid`.

When the entire pore space is filled by a single phase, we can substitute the Darcy's law into the mass balance equation to obtain the single phase flow equation



with :math:`\gamma \nabla z= \rho \boldsymbol{g}`.


.. _singlephase_discretization:
