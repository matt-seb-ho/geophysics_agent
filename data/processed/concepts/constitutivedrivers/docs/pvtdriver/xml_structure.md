**Context:** Constitutivedrivers > PVTDriver > XML Structure

## XML Structure
A typical XML file to run the driver will have several key elements. 
Here, we will walk through an example file included in the source tree at

``sh
   src/coreComponents/integrationTests/constitutiveTests/testPVT_docExample.xml

The first thing to note is that the XML file structure is identical to a standard GEOS input deck.  
In fact, once the constitutive block is calibrated, one could start adding solver and discretization blocks to the same file to create a proper field simulation.  
This makes it easy to go back and forth between calibration and simulation.

The first step is to define a parameterized fluid model to test.
Here, we create a particular type of CO2-Brine mixture:


  :language: xml
  :start-after: <!-- SPHINX_PVTDRIVER_CONSTITUTIVE_START --> 
  :end-before: <!-- SPHINX_PVTDRIVER_CONSTITUTIVE_END -->

We also define two time-history functions for the pressure (Pascal units) and temperature (Kelvin units) conditions we want to explore.


  :language: xml
  :start-after: <!-- SPHINX_PVTDRIVER_FUNCTIONS_START --> 
  :end-before: <!-- SPHINX_PVTDRIVER_FUNCTIONS_END -->

Note that the time-axis here is just a pseudo-time, allowing us to [parameterize ](https://en.wikipedia.org/wiki/Parametric_equation) arbitrarily complicated paths through a (pressure,temperature) diagram.
The actual time values have no impact on the resulting fluid properties.
Here, we fix the temperature at 350K and simply ramp up pressure from 1 MPa to 50 MPa:

A `PVTDriver` is then added as a `Task`, a particular type of executable event often used for simple actions. 


  :language: xml
  :start-after: <!-- SPHINX_PVTDRIVER_TASKS_START --> 
  :end-before: <!-- SPHINX_PVTDRIVER_TASKS_END -->

The driver itself takes as input the fluid model, the pressure and temperature control functions, and a "feed composition." 
The latter is the mole fraction of each component in the mixture to be tested.
The `steps` parameter controls how many steps are taken along the parametric (P,T) path.
Results will be written in a simple ASCII table format (described below) to the file `output`.
The `logLevel` parameter controls the verbosity of log output during execution. 
 
The driver task is added as a `SoloEvent` to the event queue.  
This leads to a trivial event queue, since all we do is launch the driver and then quit.


  :language: xml
  :start-after: <!-- SPHINX_PVTDRIVER_EVENTS_START --> 
  :end-before: <!-- SPHINX_PVTDRIVER_EVENTS_END -->

Internally, the driver uses a simple form of time-stepping to advance through the (P,T) steps. 
This timestepping is handled independently of the more complicated time-stepping pattern used by physics `Solvers` and coordinated by the `EventManager`.  
In particular, in the XML file above, the `maxTime` parameter in the `Events` block is an event manager control, controlling when/if certain events occur.  
Once launched, the PVTDriver internally determines its own max time and timestep size using a combination of the input functions' time coordinates and the requested number of loadsteps.  
It is therefore helpful to think of the driver as an instantaneous *event* (from the event manager's point of view), but one which has a separate, internal clock.
