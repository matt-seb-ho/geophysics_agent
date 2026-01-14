**Context:** Constitutive > ThreePhaseRelativePermeability > Example

# Example
```xml
   <Constitutive>
      ...
    <BrooksCoreyBakerRelativePermeability name="relperm"
                                          phaseNames="{oil, gas, water}"
                                          phaseMinVolumeFraction="{0.05, 0.05, 0.05}"
                                          waterOilRelPermExponent="{2.5, 1.5}"
                                          waterOilRelPermMaxValue="{0.8, 0.9}"
                                          gasOilRelPermExponent="{3, 3}"
                                          gasOilRelPermMaxValue="{0.4, 0.9}"/>
      ...
   </Constitutive>
