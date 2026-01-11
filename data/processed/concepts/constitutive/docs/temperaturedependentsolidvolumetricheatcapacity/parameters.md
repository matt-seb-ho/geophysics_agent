**Context:** Constitutive > TemperatureDependentSolidVolumetricHeatCapacity > Parameters

# Parameters
The temperature-dependent solid volumetric heat capacity model is called in the
`<SolidInternalEnergy>` block of the input XML file.
This model must be assigned a unique name via the
`name` attribute.
This name is used to attach the model to regions of the physical
domain via a `solidInternalEnergyModelName` attribute in the `<CompressibleSolidConstantPermeability>`
block.

The following attributes are supported:




