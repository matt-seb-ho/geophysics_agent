**Context:** Constitutive > CompositionalMultiphaseFluid > Phase labeling

## Phase labeling
Once it is confirmed that the fluid with composition :math:`z` is stable as a single phase at the current
pressure and temperature, it must be labeled as either 'liquid' or 'vapor'. This is necessary only to apply
the correct relative permeability function for calculating the phase's flow properties. The properties of the
fluid (density, viscosity) are unchanged by the assignment of the label.

Determining the mixture's true critical point is the most rigorous method for labeling. It is however expensive
and may not always be necessary. As such, a simple correlation for pseudo-critical temperature is used and this
is expected to be sufficiently accurate for correct phase labeling, except under some specific conditions.

The Li-correlation is a weighted average of the component critical temperatures and is used to determine the label
applied to the mixture. The Li pseudo-critical temperature is calcaulated as



where :math:`V_{ci}` and :math:`T_{ci}` are respectively the critical volume and temperature of component
:math:`i`. This is compared to the current temperature :math:`T` such that if :math:`T_{cp}<T` then the mixture
is labeled as vapor and as liquid otherwise.
