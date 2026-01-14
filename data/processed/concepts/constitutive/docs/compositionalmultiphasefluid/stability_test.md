**Context:** Constitutive > CompositionalMultiphaseFluid > Stability test

## Stability test
The first step is to determine if the provided mixture with total molar fractions :math:`z_c` is stable
as a single phase at the current pressure :math:`p` and temperature :math:`T`. However, this can only
be confirmed through stability testing.

The stability of a mixture is traditionally assessed using the Tangent Plane Distance (TPD) criterion
developed by Michelsen (1982a). This criterion states that a phase with composition :math:`z` is stable
at a specified pressure :math:`p` and temperature :math:`T` if and only if 



for any permissible trial composition :math:`y`, where :math:`\phi_i` denotes the fugacity
coefficient of component :math:`i`. 

To determine stability of the mixture this testing in initiated from a basic starting point, based on
Wilson K-values, to get both a lighter and a heavier trial mixture. The two trial mixtures are
calculated as :math:`y_i = z_i/K_i` and :math:`y_i = z_iK_i` where :math:`K_i` are defined by


  
where :math:`P_{ci}` and :math:`T_{ci}` are respectively, the critical pressure and temperature of
component :math:`i` and :math:`\omega_i` is the accentric factor of component :math:`i`.

The stability problem is solved by observing that a necessary condition is that :math:`g(y)` must
be non-negative at all its stationary points. The stationarity criterion can be expressed as



where :math:`h_i = \ln z_i + \ln \phi_i(z)` is a constant parameter dependent on the feed composition
:math:`z` and :math:`k` is an undetermined constant. This constant can be further incorporated into
the equation by defining the unnormalized trial phase moles :math:`Y_i` as



which reduces the stationarity criterion to



with the mole fractions :math:`y_i` related to the trial phase moles :math:`Y_i` by



With the two starting mixtures, the stationarity condition is solved using successive substitution to
determine the stationary points. If both initial states converge to a solution which has :math:`g(y)\geq 0`
then the mixture is deemed to be stable, otherwise it is deemed unstable.
