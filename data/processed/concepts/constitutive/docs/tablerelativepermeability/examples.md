**Context:** Constitutive > TableRelativePermeability > Examples

# Examples
For a two-phase water-gas system (for instance in the CO2-brine fluid model), a typical relative permeability input looks like:

``xml
   <Constitutive>
      ...
      <TableRelativePermeability
        name="relPerm"
        phaseNames="{ water, gas }"
        wettingNonWettingRelPermTableNames="{ waterRelativePermeabilityTable, gasRelativePermeabilityTable }"/>
      ...
   </Constitutive>



For a three-phase oil-water-gas system (for instance in the Black-Oil fluid model), a typical relative permeability input looks like:

``xml
   <Constitutive>
      ...
      <TableRelativePermeability
        name="relPerm"
        phaseNames="{ water, oil, gas }"
        wettingIntermediateRelPermTableNames="{ waterRelativePermeabilityTable, oilRelativePermeabilityTableForWO }"
        nonWettingIntermediateRelPermTableNames="{ gasRelativePermeabilityTable, oilRelativePermeabilityTableForGO }"/>	
      ...
   </Constitutive>



   
The tables mentioned above by name must be defined in the `<Functions>` block of the XML file using the `<TableFunction>` keyword. 
