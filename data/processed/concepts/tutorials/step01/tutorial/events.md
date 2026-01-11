**Context:** Tutorials > Step01 > Tutorial > Events

## Events
In GEOS, we call `Events` anything that happens at a set time or frequency.
Events are a central element for time-stepping in GEOS,
and a dedicated section just for events is necessary to give them the treatment they deserve.


For now, we focus on three simple events: the time at which we wish the simulation to end (`maxTime`),
the times at which we want the solver to perform updates,
and the times we wish to have simulation output values reported.


In GEOS, all times are specified in **seconds**, so here `maxTime=5000.0` means that the simulation will run from time 0 to time 5,000 seconds.


If we focus on the `PeriodicEvent` elements, we see :

 #. A **periodic solver** application: this event is named `solverApplications`. With the attribute `forceDt=20`, it tells the solver to compute results at 20-second time intervals. We know what this event does by looking at its `target` attribute: here, from time 0 to `maxTime` and with a forced time step of 20 seconds, we instruct GEOS to call the solver registered as `SinglePhaseFlow`. Note the hierarchical structure of the target formulation, using '/' to indicate a specific named instance (`SinglePhaseFlow`) of an element (`Solvers`). If the solver needs to take smaller time steps, it is allowed to do so, but it will have to compute results for every 20-second increment between time zero and `maxTime` regardless of possible intermediate time steps.
 #. An **output event**: this event is used for reporting purposes and instructs GEOS to write out results at specific frequencies. Here, we need to see results at every 100-second increment. This event triggers a full application of solvers, even if solvers were not summoned by the previous event. In other words, an output event will force an application of solvers, possibly in addition to the periodic events requested directly.


  :language: xml
  :start-after: <!-- SPHINX_TUT_INT_HEX_EVENTS -->
  :end-before: <!-- SPHINX_TUT_INT_HEX_EVENTS_END -->




.. _NumericalMethods_tag_single_phase_internal_mesh:

------------------