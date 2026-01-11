**Context:** Constitutive > TableCapillaryPressure > Parameters

# Parameters
The capillary pressure constitutive model is listed in
the `<Constitutive>` block of the input XML file.
The capillary pressure model must be assigned a unique name via
`name` attribute.
This name is used to assign the model to regions of the physical
domain via a `materialList` attribute of the `<ElementRegions>`
node.

The following attributes are supported:



Below are some comments on the model parameters.

* `phaseNames` - The number of phases can be either two or three. Supported phase names are:

===== ===========
Value Phase
===== ===========
oil   Oil phase
gas   Gas phase
water Water phase
===== ===========

* `wettingNonWettingCapPressureTableName` - The name of the capillary pressure table for two-phase systems. Note that this keyword is only valid for two-phase systems, and is not allowed for three-phase systems (for which the user must specify instead `wettingIntermediateCapPressureTableName` and `nonWettingIntermediateCapPressureTableName`). This capillary pressure must be a strictly decreasing function of the water-phase volume fraction (for oil-water systems and gas-water systems), or a strictly increasing function of the gas-phase volume fraction (for oil-gas systems).    

* `wettingIntermediateCapPressureTableName` - The name of the capillary pressure table for the pair wetting-phase--intermediate-phase. This capillary pressure is applied to the wetting phase, as a function of the wetting-phase volume fraction. Note that this keyword is only valid for three-phase systems, and is not allowed for two-phase systems (for which the user must specify instead `wettingNonWettingCapPressureTableName`). This capillary pressure must be a strictly decreasing function of the wetting-phase volume fraction.

* `nonWettingIntermediateCapPressureTableName` - The name of the capillary pressure table for the pair non-wetting-phase--intermediate-phase. Note that this keyword is only valid for three-phase systems, and is not allowed for two-phase systems (for which the user must specify instead `wettingNonWettingCapPressureTableName`). This capillary pressure must be a strictly increasing function of the non-wetting-phase volume fraction. 

