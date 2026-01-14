**Context:** Events > TasksManager > Tasks Manager Configuration

## Tasks Manager Configuration
Task
***************************
The children of the Tasks block define different Tasks to be triggered by events specified in the :ref:`EventManager` during the execution of the simulation. At present the only supported task is the `PackCollection` used to collect time history data for output by a TimeHistory output.


    :start-line: 3
    
PackCollection
***************************
The `PackCollection` Task is used to collect time history information from fields. Either the entire field or specified named sets of indices in the field can be collected.


    :start-line: 3

Note: The time history information collected via this task is buffered internally until it is output by a linked TimeHistory Output.


***************************
Triggering the Tasks
***************************
Tasks can be triggered using the :ref:`EventManager`.
Recurring tasks sould use a `<PeriodicEvent>` and one-time tasks should use a `<SoloEvent>`:

``xml
  <PeriodicEvent name="historyCollectEvent"
                 timeFrequency="1.0"
                 targetExactTimeset="1"
                 target="/Tasks/historyCollection" />

The keyword `target` has to match the `name` of a Task specified as a child of the `<Tasks>`` block.

