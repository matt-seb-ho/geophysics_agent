**Context:** Fileio > Doc > OutputTasks > TimeHistory Output

# TimeHistory Output
The TimeHistory output is defined through the `<TimeHistory>` XML node (subnode of `<Outputs> XML block`) as shown here:

```xml
  <Outputs>
    <TimeHistory name="timeHistoryOutput" sources="{/Tasks/collectionTask}" filename="timeHistory" />
  </Outputs>

The parameter options are listed in the following table:



In order to properly collect and output time history information the following steps must be accomplished:

#. Specify one or more collection tasks using the :ref:`TasksManager`.
#. Specify a `TimeHistory Output` using the collection task(s) as source(s).
#. Specify an event in the :ref:`EventManager` to trigger the collection task(s).
#. Specify an event in the :ref:`EventManager` to trigger the output.

Note: Currently if the collection and output events are triggered at the same simulation time, the one specified first will also trigger first. Thus in order to output time history for the current time in this case, always specify the time history collection events prior to the time history output events.

************************
Triggering the outputs
************************

The outputs can be triggered using the :ref:`EventManager`.
It is recommended to use a `<PeriodicEvent>` to output results with a defined frequency:

``xml
  <PeriodicEvent name="outputs"
                 timeFrequency="5000.0"
                 targetExactTimestep="1"
                 target="/Outputs/siloOutput" />

The keyword `target` has to match with the name of the `<Silo>`, `<VTK>`, or `<TimeHistory>` node.

****************************
Visualisation of the outputs
****************************

We suggest the use of VisIT_, Paraview_, and MatPlotLib_ to visualize the outputs.
