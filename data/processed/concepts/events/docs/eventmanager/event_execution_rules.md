**Context:** Events > EventManager > Event Execution Rules

## Event Execution Rules
The EventManager will repeatedly iterate through a list of candidate events specified via the Events block **in the order they are defined in the xml**.  When certain user-defined criteria are met, they will trigger and perform a task.  The simulation `cycle` denotes the number of times the primary event loop has completed, `time` denotes the simulation time at the beginning of the loop, and `dt` denotes the global timestep during the loop.

During each cycle, the EventManager will do the following:

1. Loop through each event and obtain its timestep request by considering:

   a. The maximum dt specified via the target's GetTimestepRequest method
   b. The time remaining until user-defined points (e.g. application start/stop times)
   c. Any timestep overrides (e.g. user-defined maximum dt)
   d. The timestep request for any of its children

2. Set the cycle dt to the smallest value requested by any event

3. Loop through each event and:

   a. Calculate the event `forecast`, which is defined as the expected number of cycles until the event is expected to execute.
   b. `if (forecast == 1)` the event will signal its target to prepare to execute.  This is useful for preparing time-consuming I/O operations.
   c. `if (forecast <= 0)` the event will call the Execute method on its target object

4. Check to see if the EventManager exit criteria have been met


After exiting the main event loop, the EventManager will call the `Cleanup` method for each of its children (to produce final plots, etc.).  Note: if the code is resuming from a restart file, the EventManager will pick up exactly where it left off in the execution loop.

