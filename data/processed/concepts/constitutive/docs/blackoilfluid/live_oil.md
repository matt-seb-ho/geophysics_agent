**Context:** Constitutive > BlackOilFluid > Live oil

## Live oil
The live oil fluid model make no assumptions about the partitioning of the
hydrocarbon components and the following composition matrix can be used


    y_{gv} & y_{gl} & y_{ga}\\
    \\
    y_{ov} & y_{ol} & y_{oa}\\
    \\
    y_{wv} & y_{wl} & y_{wa}
    \end{bmatrix}
    = \begin{bmatrix}
    \frac{\rho_{g}^{STC}}{\rho_{g}^{STC} + \rho_{o}^{STC} r_{s}} & \frac{\rho_{g}^{STC} R_{s}}{\rho_{o}^{STC} + \rho_{g}^{STC} R_{s}} & 0 \\
    \\
    \frac{\rho_{o}^{STC} r_{s}}{\rho_{g}^{STC} + \rho_{o}^{STC} r_{s}} & \frac{\rho_{o}^{STC}}{\rho_{o}^{STC} + \rho_{g}^{STC} R_{s}} & 0 \\
    \\
    0 & 0 & 1
    \end{bmatrix}

whereas the densities of the two hydrocarbon phases are


  \rho_{v} = & \, \frac{\rho_{g}^{STC} + \rho_{o}^{STC} R_{v}}{B_{g}}

See `Petrowiki`_ for more information.

# Parameters
Both types are represented by `<BlackOilFluid>` node in the input.
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

# Example
```xml
  <Constitutive>
    <BlackOilFluid name="fluid1"
                   fluidType="LiveOil"
                   phaseNames="{ oil, gas, water }"
                   surfaceDensities="{ 800.0, 0.9907, 1022.0 }"
                   componentMolarWeight="{ 114e-3, 16e-3, 18e-3 }"
                   tableFiles="{ pvto.txt, pvtg.txt, pvtw.txt }"/>
  </Constitutive>


.. _Petrowiki: https://petrowiki.spe.org/Phase_behavior_in_reservoir_simulation#Black-oil_PVT_models
