**Context:** Events > EventManager > Other Event Features

## Other Event Features
#### Event Progress Indicator
Because the event manager allows the user to specify the order of events, it could introduce ambiguity into the timestamps of output files.  To resolve this, we pass two arguments to the target's Execute method:

1. eventCounter (integer) - the application index for the event (or sub-event)
2. eventProgress (real64) - the percent completion of the event loop, paying attention to events whose targets are associated with physics (from the start of the event, indicated via target->GetTimestepBehavior())

For example, consider the following Events block:

``xml
  <Events maxTime="1.0e-2">
    <PeriodicEvent name="outputs"
                   timeFrequency="1e-6"
                   targetExactTimestep="0"
                   target="/Outputs/siloOutput">
    <PeriodicEvent name="solverApplications_a"
                   forceDt="1.0e-5"
                   target="/Solvers/lagsolve" />
    <PeriodicEvent name="solverApplications_b"
                   target="/Solvers/otherSolver" />
    <PeriodicEvent name="restarts"
                   timeFrequency="5.0e-4"
                   targetExactTimestep="0"
                   target="/Outputs/restartOutput"/>
  </Events>

In this case, the events solverApplications_a and solverApplications_b point target physics events.  The eventCounter, eventProgress pairs will be: outputs (0, 0.0), solverApplications_a (1, 0.0), solverApplications_b (2, 0.5), and restarts (3, 1.0).  These values are supplied to the target events via their Execute methods for use.  For example, for the name of a silo output file will have the format: "%s_%06d%02d" % (name, cycle, eventCounter), and the time listed in the file will be `time = time + dt*eventProgress`



#### Nested Events
The event manager allows its child events to be nested.  If this feature is used, then the manager follows the basic execution rules, with the following exception:  When its criteria are met, an event will first execute its (optional) target.  It will then estimate the forecast for its own sub-events, and execute them following the same rules as in the main loop.  For example:

```xml
  <Events maxTime="1.0e-2">
    <PeriodicEvent name="event_a"
                   target="/path/to/target_a" />

    <PeriodicEvent name="event_b"
                   timeFrequency="100">

      <PeriodicEvent name="subevent_b_1"
                     target="/path/to/target_b_1"/>

      <PeriodicEvent name="subevent_b_2"
                     target="/path/to/target_b_2"/>
    <PeriodicEvent/>
  </Events>

In this example, event_a will trigger during every cycle and call the Execute method on the object located at /path/to/target_a.  Because it is time-driven, event_b will execute every 100 s.  When this occurs, it will execute it will execute its own target (if it were defined), and then execute subevent_b_1 and subevent_b_2 in order. Note: these are both cycle-driven events which, by default would occur every cycle.  However, they will not execute until each of their parents, grandparents, etc. execution criteria are met as well.

