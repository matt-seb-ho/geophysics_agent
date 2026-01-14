**Context:** Constitutive > Solid > ElasticIsotropicPressureDependent > Example

# Example
A typical `Constititutive` block will look like:

```xml
  <Constitutive>
    <ElasticIsotropicPressureDependent
      name="elasticPressure"
      defaultDensity="2700"
      defaultRefPressure="-1.0"
      defaultRefStrainVol="1"
      defaultRecompressionIndex="0.003"
      defaultShearModulus="200"/>
  </Constitutive>
