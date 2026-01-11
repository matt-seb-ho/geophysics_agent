**Context:** Physicssolvers > Fluidflow > Wells > CompositionalMultiphaseWell > Primary variables

## Primary variables
The well variable formulation is the same as that of the :ref:`CompositionalMultiphaseFlow`.
In a well segment, in addition to the :math:`n_c+1` primary variables of the :ref:`CompositionalMultiphaseFlow`, namely, one pressure, :math:`p`, and
:math:`n_c` component densities, :math:`\rho_c`, we also treat the total mass flux at the interface with the next segment, denoted by :math:`q`, as a primary variable.


=========================== ===================================================
Number of primary variables Variable type
=========================== ===================================================
1                           Pressure
1                           Total mass flux at the interface with next segment
:math:`n_c`                 Component densities
=========================== ===================================================

.. _well_usage:

# Parameters
The following attributes are supported:



.. _well_input_example:

# Example

  :language: xml
  :start-after: <!-- SPHINX_COMP_WELL_SOLVER -->
  :end-before: <!-- SPHINX_COMP_WELL_SOLVER_END -->
