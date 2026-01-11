**Context:** Constitutive > TemperatureDependentSolidVolumetricHeatCapacity > Example

# Example
```xml
   <Constitutive>
      ...
      <SolidInternalEnergy
        name="rockInternalEnergy"
        referenceVolumetricHeatCapacity="4.56e6"
        dVolumetricHeatCapacity_dTemperature="1e6"
        referenceTemperature="0"
        referenceInternalEnergy="0"/>
      ...
   </Constitutive>
