**Context:** Constitutivedrivers > TriaxialDriver > XML Structure

## XML Structure
A typical XML file to run the triaxial driver will have the following key elements.  We present the whole file first, before digging into the individual blocks.


  :language: xml

The first thing to note is that the XML structure is identical to a standard GEOS input deck.  In fact, once the constitutive block is calibrated, one could start adding solver and discretization blocks to the same file to create a proper field simulation.  This makes it easy to go back and forth between calibration and simulation.

The `TriaxialDriver` is added as a `Task`, a particular type of executable event often used for simple actions.  It is added as a `SoloEvent` to the event queue.  This leads to a trivial event queue, since all we do is launch the driver and then quit.

Internally, the triaxial driver uses a simple form of time-stepping to advance through the loading steps, allowing for both rate-dependent and rate-independent models to be tested. This timestepping is handled independently from the more complicated time-stepping pattern used by physics `Solvers` and coordinated by the `EventManager`.  In particular, in the XML file above, the `maxTime` parameter in the `Events` block is an event manager control, controlling when/if certain events occur.  Once launched, the triaxial driver internally determines its own max time and timestep size using a combination of the strain function's time coordinates and the requested number of loadsteps.  It is therefore helpful to think of the driver as an instantaneous *event* (from the event manager's point of view), but one which has a separate, internal clock.

The key parameters for the TriaxialDriver are:



.. note``
   GEOS uses the *engineering* sign convention where compressive stresses and strains are *negative*.
   This is one of the most frequent issues users make when calibrating material parameters, as
   stress- and strain-like quantities often need to be negative to make physical sense.  You may note in the
   XML above, for example, that `stressFunction` and `strainFunction` have negative values for
   a compressive test.
