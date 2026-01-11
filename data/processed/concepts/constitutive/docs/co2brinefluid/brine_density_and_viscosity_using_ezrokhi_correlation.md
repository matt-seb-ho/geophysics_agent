**Context:** Constitutive > CO2BrineFluid > Brine density and viscosity using Ezrokhi correlation

## Brine density and viscosity using Ezrokhi correlation
Brine density :math:`\rho_l` is computed from pure water density :math:`\rho_w` at specified pressure and temperature corrected by Ezrokhi correlation presented in Zaytsev and Aseyev (1993):


   A(T) &= a_0 + a_1T +  a_2T^2,

where :math:`a_0, a_1, a_2` are correlation coefficients defined by user:

+------------+----------------------+-------------+-------------+-------------+
| DensityFun | EzrokhiBrineDensity  | :math:`a_0` | :math:`a_1` | :math:`a_2` |
+------------+----------------------+-------------+-------------+-------------+

While :math:`x_{CO2,\ell}` is mass fraction of CO2 component in brine, computed from molar fractions as



Pure water density is computed according to:



where :math:`c_w` is water compressibility defined as a constant :math:`4.5 \times 10^{-10} Pa^{-1}`, while :math:`\rho_{w,sat}(T)` and :math:`P_{w,sat}(T)` are density and pressure of saturated water at a given temperature.
Both are obtained through internally constructed tables tabulated as functions of temperature and filled with the steam table data from Engineering ToolBox (2003, 2004).

Brine viscosity :math:`\mu_{\ell}` is computed from pure water viscosity :math:`\mu_w` similarly:


   B(T) &= b_0 + b_1T +  b_2T^2,

where :math:`b_0, b_1, b_2` are correlation coefficients defined by user:

+--------------+------------------------+-------------+-------------+-------------+
| ViscosityFun | EzrokhiBrineViscosity  | :math:`b_0` | :math:`b_1` | :math:`b_2` |
+--------------+------------------------+-------------+-------------+-------------+

Mass fraction of CO2 component in brine :math:`x_{CO2,\ell}` is exactly as in density calculation. The dependency of pure water viscosity from pressure is ignored, and it is approximated as saturated pure water viscosity:



which is tabulated using internal table as a function of temperature based on steam table data Engineering ToolBox (2004).

   
# Parameters
The models are represented by `<CO2BrinePhillipsFluid>`, `<CO2BrineEzrokhiFluid>` nodes in the input.

The following attributes are supported:



Supported phase names are:

======== ===========
Value     Comment
======== ===========
gas      CO2 phase
water    Water phase
======== ===========

Supported component names are:

============= ===============
Value         Component
============= ===============
co2,CO2       CO2 component
water,liquid  Water component
============= ===============

# Example
``xml
    <Constitutive>
        <CO2BrinePhillipsFluid
          name="fluid"
          phaseNames="{ gas, water }"
          componentNames="{ co2, water }"
          componentMolarWeight="{ 44e-3, 18e-3 }"
          phasePVTParaFiles="{ pvtgas.txt, pvtliquid.txt }"
          flashModelParaFile="co2flash.txt"/>
    </Constitutive>


``xml
    <Constitutive>
        <CO2BrineEzrokhiFluid
          name="fluid"
          phaseNames="{ gas, water }"
          componentNames="{ co2, water }"
          componentMolarWeight="{ 44e-3, 18e-3 }"
          phasePVTParaFiles="{ pvtgas.txt, pvtliquid.txt }"
          flashModelParaFile="co2flash.txt"/>
    </Constitutive>

In the XML code listed above, "co2flash.txt" parameterizes the CO2 solubility table constructed in Step 1.
The file "pvtgas.txt" parameterizes the CO2 phase density and viscosity tables constructed in Step 2, 
the file "pvtliquid.txt" parameterizes the brine density and viscosity tables according to Phillips or Ezrokhi correlation, depending on chosen fluid model.
    
# References
- Z. Duan and R. Sun, [An improved model calculating CO2 solubility in pure
  water and aqueous NaCl solutions from 273 to 533 K and from 0 to 2000 bar.
  ](https://doi.org/10.1016/S0009-2541(02)00263-2)_, Chemical Geology,
  vol. 193.3-4, pp. 257-271, 2003.

- R. Span and W. Wagner, [A new equation of state for carbon dioxide covering
  the fluid region from the triple-point temperature to 1100 K at pressure up
  to 800 MPa ](https://aip.scitation.org/doi/abs/10.1063/1.555991)_, J. Phys.
  Chem. Ref. Data, vol. 25, pp. 1509-1596, 1996.

- A. Fenghour and W. A. Wakeham, [The viscosity of carbon dioxide
  ](https://aip.scitation.org/doi/abs/10.1063/1.556013)_, J. Phys. Chem. Ref.
  Data, vol. 27, pp. 31-44, 1998.

- S. L. Phillips et al., [A technical databook for geothermal energy
  utilization ](https://escholarship.org/content/qt5wg167jq/qt5wg167jq.pdf)_,
  Lawrence Berkeley Laboratory report, 1981.

- J. E. Garcia, Density of aqueous solutions of CO2. No. LBNL-49023.
  Lawrence Berkeley National Laboratory, Berkeley, CA, 2001.

- Zaytsev, I.D. and Aseyev, G.G. Properties of Aqueous Solutions of Electrolytes, 
  Boca Raton, Florida, USA CRC Press, 1993.

- Engineering ToolBox, [Water - Density, Specific Weight and Thermal Expansion 
  Coefficients ](https://www.engineeringtoolbox.com/water-density-specific-weight-d_595.html)_,
  2003


- Engineering ToolBox, [Water - Dynamic (Absolute) and Kinematic Viscosity 
  ](https://www.engineeringtoolbox.com/water-dynamic-kinematic-viscosity-d_596.html)_,
  2004
