**Context:** Constitutive > BrooksCoreyCapillaryPressure > Example

# Example
```xml
   <Constitutive>
      ...
      <BrooksCoreyCapillaryPressure name="capPressure"
                                    phaseNames="{oil, gas}"
                                    phaseMinVolumeFraction="{0.01, 0.015}"
                                    phaseCapPressureExponentInv="{0, 6}"
                                    phaseEntryPressure="{0, 1e8}"
                                    capPressureEpsilon="1e-8"/>
      ...
   </Constitutive>
