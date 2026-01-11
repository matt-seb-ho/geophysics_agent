**Context:** Constitutive > BrooksCoreyRelativePermeability > Examples

# Examples
For a two-phase water-gas system (for instance in the CO2-brine fluid model), a typical relative permeability input looks like:

``xml
   <Constitutive>
      ...
      <BrooksCoreyRelativePermeability
        name="relPerm"
        phaseNames="{ water, gas }"
        phaseMinVolumeFraction="{ 0.02, 0.015 }"
        phaseRelPermExponent="{ 2, 2.5 }"
        phaseRelPermMaxValue="{ 0.8, 1.0 }"/>
      ...
   </Constitutive>

For a three-phase oil-water-gas system (for instance in the Black-Oil fluid model), a typical relative permeability input looks like:

``xml
   <Constitutive>
      ...
      <BrooksCoreyRelativePermeability
        name="relPerm"
        phaseNames="{ water, oil, gas }"
        phaseMinVolumeFraction="{ 0.02, 0.1, 0.015 }"
        phaseRelPermExponent="{ 2, 2, 2.5 }"
        phaseRelPermMaxValue="{ 0.8, 1.0, 1.0 }"/>
      ...
   </Constitutive>    
