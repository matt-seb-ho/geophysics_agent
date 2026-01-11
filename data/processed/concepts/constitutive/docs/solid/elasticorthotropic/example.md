**Context:** Constitutive > Solid > ElasticOrthotropic > Example

# Example
A typical `Constititutive` block will look like:

```xml
  <Constitutive>
    <ElasticOrthotropic 
       name="shale"
       defaultDensity="2700"
       defaultNu12="0.20"
       defaultNu13="0.25"
       defaultNu23="0.30"
       defaultE1="40.0e6"
       defaultE2="50.0e6"
       defaultE3="60.0e6"
       defaultG12="20.0e6"
       defaultG13="30.0e6"
       defaultG23="40.0e6" />
  </Constitutive>
