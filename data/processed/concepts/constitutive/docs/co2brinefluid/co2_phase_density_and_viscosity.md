**Context:** Constitutive > CO2BrineFluid > CO2 phase density and viscosity

## CO2 phase density and viscosity
In GEOS, the computation of the CO2 phase density and viscosity  is entirely based on look-up in precomputed tables.
The user defines the pressure (in Pascal) and temperature (in Kelvin) axis of the density table in the form:

+------------+----------------------+-----------------+-----------------+------------------+-----------------+-----------------+------------------+
| DensityFun | SpanWagnerCO2Density | :math:`p_{min}` | :math:`p_{max}` | :math:`\Delta p` | :math:`T_{min}` | :math:`T_{max}` | :math:`\Delta T` |
+------------+----------------------+-----------------+-----------------+------------------+-----------------+-----------------+------------------+

**Parameter Descriptions**:

- **p_min**: The minimum pressure value [Pa] for which the density table is defined. It sets the lower boundary of the pressure range.
- **p_max**: The maximum pressure value [Pa] for the density table. It sets the upper boundary of the pressure range.
- **Δp (Delta p)**: The increment in pressure [Pa] between successive values in the pressure axis of the table. It defines the resolution of the pressure dimension.
- **T_min**: The minimum temperature value [K] for the density table. This sets the lower boundary of the temperature range.
- **T_max**: The maximum temperature value [K] for the density table. It sets the upper boundary of the temperature range.
- **ΔT (Delta T)**: The increment in temperature [K] between successive values in the temperature axis of the table. It defines the resolution of the temperature dimension.

This correlation is valid for pressures less than :math:`8 \times 10^8` Pascal and temperatures less than 1073.15 Kelvin.  
Using these parameters, GEOS internally constructs a two-dimensional table storing the values of density as a function of pressure and temperature.
This table is populated as explained in the work of Span and Wagner (1996) by solving the following nonlinear Helmholtz energy equation for each pair :math:`(p,T)` to obtain the value of density, :math:`\rho_{g}`:



where :math:`R` is the gas constant, :math:`\delta := \rho_{g} / \rho_{crit}` is the reduced CO2 phase density, and :math:`\tau := T_{crit} / T` is the inverse of the reduced temperature.
The definition of the residual part of the energy equation, denoted by :math:`\phi^r_{\delta}`, can be found in equation (6.5), page 1544 of Span and Wagner (1996).
The coefficients involved in the computation of :math:`\phi^r_{\delta}` are listed in Table (31), page 1544 of Span and Wagner (1996).   
These calculations are done in a preprocessing step.

The pressure and temperature axis of the viscosity table can be parameterized in a similar fashion using the format:

+--------------+----------------------+-----------------+-----------------+------------------+-----------------+-----------------+------------------+
| ViscosityFun | FenghourCO2Viscosity | :math:`p_{min}` | :math:`p_{max}` | :math:`\Delta p` | :math:`T_{min}` | :math:`T_{max}` | :math:`\Delta T` |
+--------------+----------------------+-----------------+-----------------+------------------+-----------------+-----------------+------------------+

**Parameter Descriptions**:

- **p_min**: The minimum pressure value [Pa] for which the density table is defined. It sets the lower boundary of the pressure range.
- **p_max**: The maximum pressure value [Pa] for the density table. It sets the upper boundary of the pressure range.
- **Δp (Delta p)**: The increment in pressure [Pa] between successive values in the pressure axis of the table. It defines the resolution of the pressure dimension.
- **T_min**: The minimum temperature value [K] for the density table. This sets the lower boundary of the temperature range.
- **T_max**: The maximum temperature value [K] for the density table. It sets the upper boundary of the temperature range.
- **ΔT (Delta T)**: The increment in temperature [K] between successive values in the temperature axis of the table. It defines the resolution of the temperature dimension.

This correlation is valid for pressures less than :math:`3 \times 10^8` Pascal and temperatures less than 1493.15 Kelvin.  
This table is populated as explained in the work of Fenghour and Wakeham (1998) by computing the CO2 phase viscosity, :math:`\mu_g`, as follows:


   
The "zero-density limit" viscosity, :math:`\mu_{0}(T)`, is computed as a function of temperature using equations (3), (4), and (5), as well as Table (1) of Fenghour and Wakeham (1998).
The excess viscosity, :math:`\mu_{excess}( \rho_{g}, T )`, is computed as a function of temperature and CO2 phase density (computed as explained above) using equation (8) and Table (3) of Fenghour and Wakeham (1998).
We currently neglect the critical viscosity, :math:`\mu_{crit}`.
These calculations are done in a preprocessing step.

During the simulation, the update of CO2 phase density and viscosity is simply done with a look-up in the precomputed tables. 
