**Context:** Fieldspecification > EquilibriumInitialCondition > Initialization using **FieldSpecification** tags

## Initialization using **FieldSpecification** tags
This is the initialization method illustrated in :ref:`TutorialFieldCase`.
The user can impose initial pressure, component fractions, and temperature fields using **FieldSpecification** tags, such as, for a two-component CO2-brine case:

``xml
   <FieldSpecifications>		
	     
     <FieldSpecification
       name="initialPressure"
       initialCondition="1"
       setNames="{ all }"
       objectPath="ElementRegions"
       fieldName="pressure"
       scale="1"
       functionName="initialPressureTableXYZ"/>

     <FieldSpecification
       name="initialCO2CompFraction"
       initialCondition="1"
       setNames="{ all }"
       objectPath="ElementRegions"
       fieldName="globalCompFraction"
       component="0"
       scale="1"
       functionName="initialCO2CompFracTableXYZ"/>

     <FieldSpecification
       name="initialWaterCompFrac"
       initialCondition="1"
       setNames="{ all }"
       objectPath="ElementRegions"
       fieldName="globalCompFraction"
       component="1"
       scale="1"
       functionName="initialWaterCompFracTableXYZ"/>

     <FieldSpecification
       name="initialTemperature"
       initialCondition="1"
       setNames="{ all }"
       objectPath="ElementRegions"
       fieldName="temperature"
       scale="1"
       functionName="initialTemperatureTableXYZ"/>
       
   </FieldSpecifications>		       

In this input method, `initialPressureTableXYZ`, `initialCO2CompFracTableXYZ`, `initialWaterCompFracTableXYZ`, and `initialTemperatureTableXYZ`` are tables describing these initial fields as a function of the x, y, and z spatial coordinates.
Then, the cell-wise values are determined by interpolating in these tables using the coordinates of the center of the cells.

Expected behavior:

* In this approach, it is the responsibility of the user to make sure that these initial fields satisfy a hydrostatic equilibrium. If not, the model will equilibrate itself during the first time steps of the simulation, possibly causing large initial changes in pressure, component fractions, and temperature.

* If the initial state imposed by the **FieldSpecification** tags is not at equilibrium, the displacements produced by coupled flow and mechanics simulations should be interpreted with caution, as these displacements are computed with respect to a non-equilibrium initial state.

* This method is suited to impose initial fields in complex cases currently not supported by the **HydrostaticEquilibrium** tag (e.g., in the presence of phase contacts, capillary pressure, etc). Specifically, the user can equilibrate the model using other means (such as using another simulator, or running a few steps of GEOS), retrieve the equilibrated values, convert them into x-y-z tables, and impose them in the new GEOS simulations using **FieldSpecification** tags.  
