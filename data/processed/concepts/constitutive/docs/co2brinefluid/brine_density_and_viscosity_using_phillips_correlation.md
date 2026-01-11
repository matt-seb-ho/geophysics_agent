**Context:** Constitutive > CO2BrineFluid > Brine density and viscosity using Phillips correlation

## Brine density and viscosity using Phillips correlation
The computation of the brine density involves a tabulated correlation presented in Phillips et al. (1981). 
The user specifies the (constant) salinity and defines the pressure and temperature axis of the brine density table in the form:

+------------+----------------------+-----------------+-----------------+------------------+-----------------+-----------------+------------------+----------+
| DensityFun | PhillipsBrineDensity | :math:`p_{min}` | :math:`p_{max}` | :math:`\Delta p` | :math:`T_{min}` | :math:`T_{max}` | :math:`\Delta T` | Salinity | 
+------------+----------------------+-----------------+-----------------+------------------+-----------------+-----------------+------------------+----------+

**Parameter Descriptions**:

- **p_min**: The minimum pressure value [Pa] for which the density table is defined. It sets the lower boundary of the pressure range.
- **p_max**: The maximum pressure value [Pa] for the density table. It sets the upper boundary of the pressure range.
- **Δp (Delta p)**: The increment in pressure [Pa] between successive values in the pressure axis of the table. It defines the resolution of the pressure dimension.
- **T_min**: The minimum temperature value [K] for the density table. This sets the lower boundary of the temperature range.
- **T_max**: The maximum temperature value [K] for the density table. It sets the upper boundary of the temperature range.
- **ΔT (Delta T)**: The increment in temperature [K] between successive values in the temperature axis of the table. It defines the resolution of the temperature dimension.
- **Salinity**: Salinity is expressed in molality (moles of NaCl per kg of brine).

The pressure must be in Pascal and must be less than :math:`5 \times 10^7` Pascal.
The temperature must be in Kelvin and must be between 283.15 and 623.15 Kelvin.
Using these parameters, GEOS performs a preprocessing step to construct a two-dimensional table storing the brine density, :math:`\rho_{\ell,table}` for the specified salinity as a function of pressure and temperature using the expression:

.. math```
   \rho_{\ell,table} &= A + B x + C x^2 + D x^3 \\
   x &= c_1 \exp( a_1 m ) + c_2 \exp( a_2 T ) + c_3 \exp( a_3 P )

We refer the reader to Phillips et al. (1981), equations (4) and (5), pages 14 and 15 for the definition of the coefficients involved in the previous equation.
This concludes the preprocessing step.

Then, during the simulation, the brine density update proceeds in two steps.
First, a table look-up is performed to retrieve the value of density, :math:`\rho_{\ell,table}`.
Then, in a second step, the density is modified using the method of Garcia (2001) to account for the presence of CO2 dissolved in brine as follows:

.. math```
   \rho_{\ell} = \rho_{\ell,table} + M_{CO2} c_{CO2} - c_{CO2} \rho_{\ell,table} V_{\phi}

where :math:`M_{CO2}` is the molecular weight of CO2, :math:`c_{CO2}` is the concentration of CO2 in brine, and :math:`V_{\phi}` is the apparent molar volume of dissolved CO2.
The CO2 concentration in brine is obtained as:

.. math```
   c_{CO2} = \frac{y_{CO2,\ell} \rho_{\ell,table}}{M_{H2O}(1-y_{CO2,\ell})} 

where :math:`M_{H2O}` is the molecular weight of water. 
The apparent molar volume of dissolved CO2 is computed as a function of temperature using the expression:

.. math```
   V_{\phi} = 37.51 - 9.585 \times 10^{-2} T + 8.740 \times 10^{-4} T^2 - 5.044 \times 10^{-7} T^3

The brine viscosity is controlled by a salinity parameter provided by the user in the form:

+--------------+------------------------+----------+
| ViscosityFun | PhillipsBrineViscosity | Salinity |
+--------------+------------------------+----------+

During the simulation, the brine viscosity is updated as a function of temperature using the analytical relationship of Phillips et al. (1981):



where the coefficients :math:`a` and :math:`b` are defined as:


   b &= \mu_{w}(T) (1.0 + 0.0816 m + 0.0122 m^2 + 0.000128 m^3) 
   
where :math:`\mu_{w}` is the pure water viscosity computed as a function of temperature,
and :math:`m` is the user-defined salinity (in moles of NaCl per kg of brine).

