**Context:** Constitutive > SlipDependentPermeability > Example

# Example
```xml
   <Constitutive>
      ...
      <SlipDependentPermeability 
        name="fracturePerm"
        shearDispThreshold="0.005"
        maxPermMultiplier="1000.0"
        initialPermeability="{1e-15, 1e-15, 1e-15}"/>
      ...
   </Constitutive>
