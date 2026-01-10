**Context:** Constitutive > Solid > ElasticTransverseIsotropic > Example

# Example
A typical `Constititutive` block will look like:

```xml
  <Constitutive>
    <ElasticTransverseIsotropic 
       name="shale"
       defaultDensity="2700"
       defaultPoissonRatioAxialTransverse="0.20"
       defaultPoissonRatioTransverse="0.30"
       defaultYoungModulusAxial="50.0e6"
       defaultYoungModulusTransverse="60.0e6"
       defaultShearModulusAxialTransverse="30.0e6" />
  </Constitutive>

