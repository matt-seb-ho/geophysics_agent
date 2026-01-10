**Context:** Constitutive > TemperatureDependentThermalConductivity > Example

# Example
```xml
   <Constitutive>
      ...
      <SinglePhaseThermalConductivity
        name="thermalCond_nonLinear"
        defaultThermalConductivityComponents="{ 1.5, 1.5, 1.5 }"
        thermalConductivityGradientComponents="{ -12e-4, -12e-4, -12e-4 }"
        referenceTemperature="20"/>
      ...
   </Constitutive>
