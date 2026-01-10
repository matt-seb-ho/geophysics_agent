**Context:** Physicssolvers > Fluidflow > CompositionalMultiphaseFlow > Discretization

## Discretization
### Spatial Discretization
The governing equations are discretized using standard cell-centered finite-volume
discretization.

In the approximation of the flux term at the interface between two control volumes,
the calculation of the pressure stencil is general and will ultimately support a
Multi-Point Flux Approximation (MPFA) approach. The current implementation of the
transmissibility calculation is reviewed in the section about
:doc:`/coreComponents/discretizationMethods/docs/NumericalMethodsManager`.

The approximation of the dynamic transport coefficients multiplying the discrete
potential difference (e.g., the phase mobilities) is performed with a first-order
phase-per-phase single-point upwinding based on the sign of the phase potential difference
at the interface.

### Temporal Discretization
The compositional multiphase solver uses a fully implicit (backward Euler) temporal discretization.

.. _solution_strategy:
