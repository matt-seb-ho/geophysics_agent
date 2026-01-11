**Context:** Fileio > Doc > OutputTasks > Visualizing VTK outputs with VisIT

# Visualizing VTK outputs with VisIT
If the `<VTK>` XML node was defined, GEOS writes the results in a folder named after the `plotFileRoot` attribute (default = `vtkOutputs``).
For problems with multiple active regions (e.g. :ref:`TutorialHydraulicFractureWithAdvancedXML`), additional work may be required to ensure that vtk files can be read by VisIt.
Options include:

1. Using a VisIt macro / python script to convert default multi-region vtk files (see `GEOS/src/coreComponents/python/visitMacros/visitVTKConversion.py`).
2. Using the `outputRegionType` attribute to output separate sets of files per region.  For example:

``xml
  <Problem>
    <Events>
      <!-- Use nested events to trigger both vtk outputs -->
      <PeriodicEvent
        name="outputs"
        timeFrequency="2.0"
        targetExactTimestep="0">
        <PeriodicEvent
          name="outputs_cell"
          target="/Outputs/vtkOutput_cell"/>
        <PeriodicEvent
          name="outputs_surface"
          target="/Outputs/vtkOutput_surface"/>
      </PeriodicEvent>
    </Events>
    
    <Outputs>
      <VTK
        name="vtkOutput_cell"
        outputRegionType="cell"
        plotFileRoot="vtk_cell"/>

      <VTK
        name="vtkOutput_surface"
        outputRegionType="surface"
        plotFileRoot="vtk_surface"/>
    </Outputs>
  </Problem>


In VisIt, the prepared files can be visualized as follows:

1. Click the Open icon (or select File/Open from the top menu).
2. Enter the vtk output folder in the left-hand panel (these will be separate if you use option 2 above).
3. Select the desired `*.vtm` group in the right-hand panel (by double-clicking or selecting OK).
4. (Repeat for any additional datasets/regions.)
5. In the main window, select the desired dataset from the Active Sources dropdown menu.
6. Click on the Add icon, and select a parameter to visualize from the mesh, psuedocolor, or vector plot options
7. At some point you may be prompted to create a Database Correlation.  If you select Yes, then VisIt will create a new time slider, which can be used to change the time state while keeping the various aspects of the simulation synchronized.
8. Finally, click the Draw button and use the time slider to visualize the output.

Please consult the VisIT_ documentation for further explanations on its usage.

