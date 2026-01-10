**Context:** Fileio > Doc > OutputTasks > Visualizing TimeHistory outputs with MatPlotLib

# Visualizing TimeHistory outputs with MatPlotLib
If the `<TimeHistory>` XML node was defined, GEOS writes a file named after the string defined
in the `filename` keyword and formatted as specified by the string defined in the `format``
keyword (only HDF5_ is currently supported).

The TimeHistory file contains the collected time history information from each specified time history collector.
This information includes datasets for the time itself, any metadata sets describing index association with specified
collection sets, and the time history information itself.

It is recommended to use MatPlotLib_ and format-specific accessors (like H5PY for HDF5_) to access and easily plot the
time history datat.

.. _SILO: https://wci.llnl.gov/simulation/computer-codes/silo
.. _VTK: https://vtk.org/wp-content/uploads/2015/04/file-formats.pdf
.. _HDF5: https://portal.hdfgroup.org/display/HDF5/HDF5
.. _VisIT: https://wci.llnl.gov/simulation/computer-codes/visit/downloads
.. _Paraview: https://www.paraview.org/
.. _MatPlotLib: https://matplotlib.org/
