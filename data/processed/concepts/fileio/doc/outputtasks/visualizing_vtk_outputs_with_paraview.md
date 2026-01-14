**Context:** Fileio > Doc > OutputTasks > Visualizing VTK outputs with Paraview

# Visualizing VTK outputs with Paraview
If the `<VTK>` XML node was defined, GEOS writes a folder and a `.pvd` file named after the string defined
in `name` keyword.

The `.pvd` file contains references to the `.pvtu` files. One `.pvtu` file is output according the frequency defined in the `timeFrequency` keyword of the Event that has triggered the output.

One `.pvtu` contains references to `.vtu` files. There is as much `.vtu` file as there were MPI processes
used for the computation.

All these files can be opened with paraview. To have the whole results for every output time steps, you can
open the `.pvd` file.
