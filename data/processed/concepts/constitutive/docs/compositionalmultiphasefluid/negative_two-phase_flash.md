**Context:** Constitutive > CompositionalMultiphaseFluid > Negative two-phase flash

## Negative two-phase flash
When a cell is identified as having an unstable mixture, it is necessary to determine the amounts in the liquid
and vapor phases through phase splitting. This phase split is calculated by ensuring that the two phases are
in thermodynamic equilibrium. For a system to be in thermodynamic equilibrium, the fugacities of each component
in both the liquid and vapor phases must be equal:



where :math:`\phi_{iL}` is the fugacity of component :math:`i` in the liquid phase and :math:`\phi_{iL}` is the
fugacity of component :math:`i` in the vapor phase.

Fugacities are functions of temperature, pressure, and composition:



and 



and are calculated directly from an equation of state.

Equilibrium constants, also known as K-values, are defined for each component as:



where :math:`x_i` is the mole fraction of component :math:`i` in the liquid phase and :math:`y_i` is the
mole fraction of component :math:`i` in the vapor phase. If we denote :math:`V` as the mole fraction
of the vapor phase, the material balance indicates that the mole fractions of each component in the liquid
and vapor phases are given by:



and



The value of :math:`V` corresponding to a given set of K-values is determined by solving the
so called Rachford and-Rice equation:



The flash calculation process is as follows:

#. Once the mixture is confirmed to be stable, an initial set of K-values is chosen, typically using Wilson's formula.

#. Given :math:`z_i` and :math:`K_i`, the Rachford-Rice equation is solved to determine the molar fraction of vapor,  :math:`V`. This is initially solved using successive substitution, followed by Newton iterations once the residual is sufficiently reduced.

#. After  :math:`V` is calculated, the corresponding liquid and vapor mole fractions, :math:`x_i` and :math:`y_i`, are computed.

#. These phase compositions are then used to calculate the component fugacities :math:`\phi_{iL}` and :math:`\phi_{iV}` in the liquid and vapor phases using the equation of state.

#. Convergence is reached when the fugacities are equal for all components. The convergence criterion is defined as:

   
   
   where :math:`\varepsilon` is the convergence tolerance.

#. If convergence is not achieved, successive substitution is used to update the set of K-values for the next iteration. The new K-values at iteration  :math:`t+1` are given by:

   

# Parameters
The model represented by `<CompositionalMultiphaseFluid>` node in the input.
Under the hood this is a wrapper around `PVTPackage` library, which is included as a submodule.
In order to use the model, GEOS must be built with `-DENABLE_PVTPACKAGE=ON` (default).

The following attributes are supported:



Supported phase names are:

===== ===========
Value Comment
===== ===========
oil   Oil phase
gas   Gas phase
water Water phase
===== ===========

Supported Equation of State types:

===== =======================
Value Comment
===== =======================
PR    Peng-Robinson EOS
SRK   Soave-Redlich-Kwong EOS
===== =======================

# Example
```xml
  <Constitutive>
    <CompositionalMultiphaseFluid name="fluid1"
                                  phaseNames="{ oil, gas }"
                                  equationsOfState="{ PR, PR }"
                                  componentNames="{ N2, C10, C20, H2O }"
                                  componentCriticalPressure="{ 34e5, 25.3e5, 14.6e5, 220.5e5 }"
                                  componentCriticalTemperature="{ 126.2, 622.0, 782.0, 647.0 }"
                                  componentAcentricFactor="{ 0.04, 0.443, 0.816, 0.344 }"
                                  componentMolarWeight="{ 28e-3, 134e-3, 275e-3, 18e-3 }"
                                  componentVolumeShift="{ 0, 0, 0, 0 }"
                                  componentBinaryCoeff="{ { 0, 0, 0, 0 },
                                                        { 0, 0, 0, 0 },
                                                        { 0, 0, 0, 0 },
                                                        { 0, 0, 0, 0 } }"/>
  </Constitutive>

# References
- M. L. Michelsen, [The Isothermal Flash Problem. Part I. Stability.
  ](https://doi.org/10.1016/0378-3812(82)85001-2)_, Fluid Phase Equilibria,
  vol. 9.1, pp. 1-19, 1982a.

- M. L. Michelsen, [The Isothermal Flash Problem. Part II. Phase-Split Calculation.
  ](https://doi.org/10.1016/0378-3812(82)85002-4)_, Fluid Phase Equilibria,
  vol. 9.1, pp. 21-40, 1982b.

.. _Petrowiki: https://petrowiki.spe.org/Phase_behavior_in_reservoir_simulation#Equation-of-state_models
