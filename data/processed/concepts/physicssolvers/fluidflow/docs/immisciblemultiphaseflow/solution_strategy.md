**Context:** Physicssolvers > Fluidflow > ImmiscibleMultiphaseFlow > Solution Strategy

## Solution Strategy
The nonlinear solution strategy is based on Newton's method.
At each Newton iteration, the solver assembles a residual vector, :math:`R`,
collecting the :math:`n_p` discrete mass conservation equations and the volume
constraint for all the control volumes.

.. _immiscible_parameters:

# Parameters
The following attributes are supported:



.. _immiscible_input_example:

# Example

   :language: xml
   :start-after: <!-- START_SPHINX_INCLUDE_SOLVER_BLOCK -->
   :end-before: <!-- END_SPHINX_INCLUDE_SOLVER_BLOCK -->

