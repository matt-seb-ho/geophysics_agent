**Context:** Fieldspecification > EquilibriumInitialCondition > Initialization using **HydrostaticEquilibrium**

## Initialization using **HydrostaticEquilibrium**
This is the initialization procedure that we have described in the first sections of this page.
In **HydrostaticEquilibrium**, the initial component fractions and temperatures are provided as a function of elevation only, and the hydrostatic pressure is computed internally before the simulation starts.
The typical input was illustrated for a CO2-brine fluid model in the previous paragraph.

Expected behavior:

* If **FieldSpecification** tags specifying initial pressure, component fractions, and/or temperature are included in an XML input file that also contains the **HydrostaticEquilibrium** tag, the **FieldSpecification** tags are ignored by GEOS. In other words, only the pressure, component fractions, and temperature fields defined with the **HydrostaticEquilibrium** tag as a function of elevation are taken into account.

* In the absence of source/sink terms and wells, the initial flow residual should be smaller than :math:`10^-6`. Similarly, in coupled simulations, the residual of the mechanical problem should be close to zero.
