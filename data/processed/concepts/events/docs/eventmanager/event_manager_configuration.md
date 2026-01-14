**Context:** Events > EventManager > Event Manager Configuration

## Event Manager Configuration
#### Event
The children of the Event block define the events that may execute during a simulation.  These may be of type `HaltEvent`, `PeriodicEvent`, or `SoloEvent`.  The exit criteria for the global event loop are defined by the attributes `maxTime` and `maxCycle` (which by default are set to their max values).  If the optional logLevel flag is set, the EventManager will report additional information with regards to timestep requests and event forecasts for its children.


    :start-line: 3

#### PeriodicEvent
This is the most common type of event used in GEOS.  As its name suggests, it will execute periodically during a simulation.  It can be triggered based upon a user-defined `cycleFrequency` or `timeFrequency`.

If cycleFrequency is specified, the event will attempt to execute every X cycles.  Note: the default behavior for a PeriodicEvent is to execute every cycle.  The event forecast for this case is given by: `forecast = cycleFrequency - (cycle - lastCycle)` .

If timeFrequency is specified, the event will attempt to execute every X seconds (this will override any cycle-dependent behavior).  By default, the event will attempt to modify its timestep requests to respect the timeFrequency (this can be turned off by specifying targetExactTimestep="0").  The event forecast for this case is given by: `if (dt > 0), forecast = (timeFrequency - (time - lastTime)) / dt, otherwise forecast=max`

By default, a PeriodicEvent will execute throughout the entire simulation.  This can be restricted by specifying the beginTime and/or endTime attributes.  Note: if either of these values are set, then the event will modify its timestep requests so that a cycle will occur at these times (this can be turned off by specifying targetExactStartStop="0").

The timestep request event is typically determined via its target.  However, this value can be overridden by setting the `forceDt` or `maxEventDt` attributes.


    :start-line: 3

#### SoloEvent
This type of event will execute once once the event loop reaches a certain cycle (targetCycle) or time (targetTime).  Similar to the PeriodicEvent type, this event will modify its timestep requests so that a cycle occurs at the exact time requested (this can be turned off by specifying targetExactTimestep="0").  The forecast calculations follow an similar approach to the PeriodicEvent type.


    :start-line: 3

#### HaltEvent
This event type is designed to track the wall clock.  When the time exceeds the value specified via maxRunTime, the event will trigger and set a flag that instructs the main EventManager loop to cleanly exit at the end of the current cycle.  The event for cast for this event type is given by: `forecast = (maxRuntime - (currentTime - startTime)) / realDt`


    :start-line: 3


