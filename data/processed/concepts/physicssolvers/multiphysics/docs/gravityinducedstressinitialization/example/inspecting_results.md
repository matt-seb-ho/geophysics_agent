**Context:** Physicssolvers > Multiphysics > Gravityinducedstressinitialization > Example > Inspecting Results

## Inspecting Results
In the example, we request vtk output files for time-series (time history). We use paraview to visualize the outcome at the time 0s.
The following figure shows the final gradient of pressure and of the effective vertical stress after initialization is completed.

.. _problemInitializationPressure:

   :align: center
   :width: 500
   :figclass: align-center

   Simulation result of pressure

.. _problemInitializationStressZZ:

   :align: center
   :width: 500
   :figclass: align-center

   Simulation result of effective vertical stress


The figure below shows the comparison between the total stress computed by GEOS(marks) and with an analytical solutions (solid lines). Note that, because of the use of an isotropic model, the minimum and maximul horizontal stresses are equal.




------------------------------------------------------------------