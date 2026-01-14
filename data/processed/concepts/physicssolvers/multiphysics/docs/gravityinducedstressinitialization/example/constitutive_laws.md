**Context:** Physicssolvers > Multiphysics > Gravityinducedstressinitialization > Example > Constitutive Laws

## Constitutive Laws
A homogeneous domain with one solid material is assumed, and its mechanical and fluid properties are specified in the `Constitutive` section: 


    :language: xml
    :start-after: <!-- SPHINX_MATERIAL -->
    :end-before: <!-- SPHINX_MATERIAL_END -->


As shown above, in the `CellElementRegion` section, 
`rock` is the solid material in the computational domain and `water` is the fluid material. 
Here, Porous Elastic Isotropic model `PorousElasticIsotropic` is used to simulate the elastic behavior of `rock`.
As for the solid material parameters, `defaultDensity`, `defaultPoissonRatio`, `defaultYoungModulus`, `grainBulkModulus`, `defaultReferencePorosity`, and `permeabilityComponents` denote the rock density, Poisson ratio, Young modulus, grain bulk modulus, porosity, and permeability components respectively. In additon, the fluid property (`water`) of density, viscosity, compressibility and viscosibility are specified with `defaultDensity`, `defaultViscosity`, `compressibility`, and `viscosibility`. 
All properties are specified in the International System of Units.


------------------------------