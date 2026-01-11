**Context:** Constitutive > TableRelativePermeability > Parameters

# Parameters
The relative permeability constitutive model is listed in
the `<Constitutive>` block of the input XML file.
The relative permeability model must be assigned a unique name via
`name` attribute.
This name is used to assign the model to regions of the physical
domain via a `materialList` attribute of the `<ElementRegions>`
node.

The following attributes are supported:



Below are some comments on the model parameters.

* `phaseNames` - The number of phases can be either two or three. For three-phase flow, this model applies a Baker interpolation to the intermediate phase relative permeability. Supported phase names are:

===== ===========
Value Phase
===== ===========
oil   Oil phase
gas   Gas phase
water Water phase
===== ===========

* `wettingNonWettingRelPermTableNames` - The list of relative permeability table names for two-phase systems, starting with the name of the wetting-phase relative permeability table, followed by the name of the non-wetting phase relative permeability table. Note that this keyword is only valid for two-phase systems, and is not allowed for three-phase systems (for which the user must specify instead `wettingIntermediateRelPermTableNames` and `nonWettingIntermediateRelPermTableNames`).  

* `wettingIntermediateRelPermTableNames` - The list of relative permeability table names for the pair wetting-phase--intermediate-phase, starting with the name of the wetting-phase relative permeability table, and continuing with the name of the intermediate phase relative permeability table. Note that this keyword is only valid for three-phase systems, and is not allowed for two-phase systems (for which the user must specify instead `wettingNonWettingRelPermTableNames`).  

* `nonWettingIntermediateRelPermTableNames` - The list of relative permeability table names for the pair non-wetting-phase--intermediate-phase, starting with the name of the non-wetting-phase relative permeability table, and continuing with the name of the intermediate phase relative permeability table. Note that this keyword is only valid for three-phase systems, and is not allowed for two-phase systems (for which the user must specify instead `wettingNonWettingRelPermTableNames`).  


