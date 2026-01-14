**Context:** Physicssolvers > Multiphysics > Usertablestressinitialization > Example > Inspecting Results

## Inspecting Results
In the example, we request vtk output files for time-series (time history). We use paraview to visualize the outcome at the time 0s.
The following figure shows the final gradient of pressure and of the effective vertical stress after initialization is completed.

.. _problemInitializationPres:

    :align: center
    :width: 500
    :figclass: align-center

    Simulation result of pressure

.. _problemInitializationSZZ:

    :align: center
    :width: 500
    :figclass: align-center

    Simulation result of effective vertical stress

The figure below shows the comparisons between the numerical predictions (marks) and the corresponding user-provided stress gradients. Note that anisotropic horizontal stresses are obtained through this intialization procedure; however, mechanical equilibrium might not be guaranteed, especially for the heterogeneous models.




------------------------------------------------------------------