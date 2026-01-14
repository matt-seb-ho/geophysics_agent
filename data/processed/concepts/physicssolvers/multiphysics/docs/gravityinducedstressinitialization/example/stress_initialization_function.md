**Context:** Physicssolvers > Multiphysics > Gravityinducedstressinitialization > Example > Stress Initialization Function

## Stress Initialization Function
In the `Tasks` section, `SinglePhasePoromechanicsInitialization` tasks are defined to initialize the model by calling the poro-mechanics solver `poroSolve`. This task is used to determine stress gradients through designated densities and established constitutive relationships to maintain mechanical equilibrium and reset all initial displacements to zero following the initialization process.  


    :language: xml
    :start-after: <!-- SPHINX_TASKS -->
    :end-before: <!-- SPHINX_TASKS_END -->
    
The initialization is triggered into action using the `Event` management section, where the `soloEvent` function calls the task at the target time (in this case -1e10s).
 

    :language: xml
    :start-after: <!-- SPHINX_EVENTS -->
    :end-before: <!-- SPHINX_EVENTS_END -->

The `PeriodicEvent` function is used here to define recurring tasks that progress for a stipulated time during the simuation. We also use it in this example to save the vtkOuput results.


    :language: xml
    :start-after: <!-- SPHINX_OUTPUT -->
    :end-before: <!-- SPHINX_OUTPUT_END -->

We use Paraview to extract the data from the vtkOutput files at the initialization time, and then use a Python script to read and plot the stress and pressure gradients for verification and visualization.



-----------------------------------