**Context:** Constitutive > TableCapillaryPressure > Examples

# Examples
For a two-phase water-gas system (for instance in the CO2-brine fluid model), a typical capillary pressure input looks like:

``xml
   <Constitutive>
      ...
      <TableCapillaryPressure
        name="capPressure"
        phaseNames="{ water, gas }"
        wettingNonWettingCapPressureTableNames="waterCapillaryPressureTable"/>
      ...
   </Constitutive>

For a three-phase oil-water-gas system (for instance in the Black-Oil fluid model), a typical capillary pressure input looks like:

``xml
   <Constitutive>
      ...
      <TableCapillaryPressure
        name="capPressure"
        phaseNames="{ water, oil, gas }"
        wettingIntermediateCapPressureTableName="waterCapillaryPressureTable"
        nonWettingIntermediateCapPressureTableName="gasCapillaryPressureTable"/>	
      ...
   </Constitutive>

The tables mentioned above by name must be defined in the `<Functions>` block of the XML file using the `<TableFunction>` keyword. 
