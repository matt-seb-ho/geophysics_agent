**Context:** Constitutivedrivers > TriaxialDriver > Test Modes

## Test Modes
The most complicated part of the driver is understanding how the stress and strain functions are applied in different testing modes.  The driver mimics laboratory core tests, with loading controlled in the
axial and radial directions. These conditions may be either strain-controlled or stress-controlled, with the user providing time-dependent functions to describe the loading.  The following table describes the available test modes in detail:

+--------------------+-------------------------+--------------------------+---------------------------+
| **mode**           | **axial loading**       | **radial loading**       | **initial stress**        |
+--------------------+-------------------------+--------------------------+---------------------------+
| `strainControl`  | axial strain controlled | radial strain controlled | isotropic stress using    |
|                    | with `axialControl`   | with `radialControl`   | `initialStress`         |
+--------------------+-------------------------+--------------------------+---------------------------+
| `stressControl`  | axial stress controlled | radial stress controlled | isotropic stress using    |
|                    | with `axialControl`   | with `radialControl`   | `initialStress`         |
+--------------------+-------------------------+--------------------------+---------------------------+
| `mixedControl`   | axial strain controlled | radial stress controlled | isotropic stress using    |
|                    | with `axialControl`   | with `radialControl`   | `initialStress`         |
+--------------------+-------------------------+--------------------------+---------------------------+

Note that a classical triaxial test can be described using either the `stressControl` or `mixedControl` mode.  We recommend using the `mixedControl` mode when possible, because this almost always leads to well-posed loading conditions.  In a pure stress controlled test, it is possible for the user to request that the material sustain a load beyond its intrinsic strength envelope, in which case there is no feasible solution and the driver will fail to converge.  Imagine, for example, a perfectly plastic material with a yield strength of 10 MPa, but the user attempts to load it to 11 MPa.  

A volumetric test can be created by setting the axial and radial control functions to the same time history function.  Similarly, an oedometer test can be created by setting the radial strain to zero. 

The user should be careful to ensure that the initial stress set via the `initialStress` value is consistent any applied stresses set through axial or radial loading functions.  Otherwise, the material may experience sudden and unexpected deformation at the first timestep because it is not in static equilibrium.
