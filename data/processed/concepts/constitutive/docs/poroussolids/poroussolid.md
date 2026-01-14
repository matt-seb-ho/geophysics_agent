**Context:** Constitutive > PorousSolids > PorousSolid

# PorousSolid
To run poromechanical problems, the total stress is decomposed into an "effective stress" (driven by mechanical deformations) and a pore fluid
pressure component, following the [Biot theory of poroelasticity ](https://doi.org/10.1016/B978-0-08-040615-2.50011-3)_.
For single-phase flow, or multiphase problems with no capillarity, this decomposition reads



where :math:`\sigma_{ij}` is the :math:`ij` component of the total stress tensor,
:math:`\sigma\prime_{ij}` is the :math:`ij` component of the effective (Cauchy) stress tensor,
:math:`b` is Biot's coefficient,
:math:`p` is fluid pressure,
and :math:`\delta` is the Kronecker delta.

The `PorousSolid` models simply append the keyword Porous in front of the solid model they contain,
e.g., PorousElasticIsotropic, PorousDruckerPrager, and so on. Additionally, they require to
define a `BiotPorosity` model and a `ConstantPermeability` model. For example, a Poroelastic material
with a certain permeability can be defined as

```xml
   <Constitutive>
     <PorousElasticIsotropic name="porousRock"
                             porosityModelName="rockPorosity"
                             solidModelName="rockSkeleton"
                             permeabilityModelName="rockPermeability"/>

     <ElasticIsotropic name="rockSkeleton"
                       defaultDensity="0"
                       defaultYoungModulus="1.0e4"
                       defaultPoissonRatio="0.2"/>

     <BiotPorosity name="rockPorosity"
                   grainBulkModulus="1.0e27"
                   defaultReferencePorosity="0.3"/>

     <ConstantPermeability name="rockPermeability"
                        permeabilityComponents="{ 1.0e-4, 1.0e-4, 1.0e-4 }"/>
   </Constitutive>

Note that any of the previously described solid models is used by the `PorousSolid` model
to compute the effective stress, leading to either poro-elastic, poro-plastic, or poro-damage
behavior depending on the specific model chosen.
