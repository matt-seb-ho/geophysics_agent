**Context:** Constitutive > VanGenuchtenCapillaryPressure > Example

# Example
```xml
    <Constitutive>
       ...
       <VanGenuchtenCapillaryPressure name="capPressure"
                                      phaseNames="{ water, oil }"
                                      phaseMinVolumeFraction="{ 0.1, 0.015 }"
                                      phaseCapPressureExponentInv="{ 0.55, 0 }"
                                      phaseCapPressureMultiplier="{ 1e6, 0 }"
                                      capPressureEpsilon="1e-7"/>
      ...
    </Constitutive>
