**Context:** Tutorials > Step03 > Tutorial > Events

## Events
The events are used here to guide the simulation through time,
and specify when outputs must be triggered.


  :language: xml
  :start-after: <!-- SPHINX_FIELD_CASE_EVENTS -->
  :end-before: <!-- SPHINX_FIELD_CASE_EVENTS_END -->

The **Events** tag is associated with the `maxTime` keyword defining the maximum time.
If this time is ever reached or exceeded, the simulation ends.

Two `PeriodicEvent` are defined.
- The first one, `solverApplications`, is associated with the solver. The  `forceDt` keyword means that there will always be time-steps of 10e6 seconds.
- The second, `outputs`, is associated with the output. The `timeFrequency` keyword means that it will be executed every 10e6 seconds.


.. _NumericalMethods_tag_field_case:

------------------