**Context:** Constitutive > PorousSolids > CompressibleSolid

# CompressibleSolid
This composite constitutive model requires to define a `NullModel` as solid model (since
no mechanical properties are used), a `PressurePorosity` model and any type of `Permeability` model.

To define this composite model the keyword `CompressibleSolid` has to be appended to the name
of the permeability model of choice, as shown in the following example for the `ConstantPermeability` model.


```xml
   <Constitutive>
     <CompressibleSolidConstantPermeability name="porousRock"
                                            solidModelName="nullSolid"
                                            porosityModelName="rockPorosity"
                                            permeabilityModelName="rockPermeability"/>

    <NullModel name="nullSolid"/>

    <PressurePorosity name="rockPorosity"
                      referencePressure="1.0e27"
                      defaultReferencePorosity="0.3"
                      compressibility="1.0e-9"/>

    <ConstantPermeability name="rockPermeability"
                          permeabilityComponents="{ 1.0e-4, 1.0e-4, 1.0e-4 }"/>

   </Constitutive>

