**Context:** Physicssolvers > Fluidflow > CompositionalMultiphaseFlow > Solution Strategy

## Solution Strategy
The nonlinear solution strategy is based on Newton's method.
At each Newton iteration, the solver assembles a residual vector, :math:`R`,
collecting the :math:`n_c` discrete mass conservation equations and the volume
constraint for all the control volumes.

.. _parameters:

# Parameters
The following attributes are supported:



.. _input_example:

# Example

   :language: xml
   :start-after: <!-- START_SPHINX_INCLUDE_SOLVER_BLOCK -->
   :end-before: <!-- END_SPHINX_INCLUDE_SOLVER_BLOCK -->

We refer the reader to :ref:`TutorialDeadOilBottomLayersSPE10` for a complete tutorial illustrating the use of this solver.
