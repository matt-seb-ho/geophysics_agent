**Context:** Constitutive > VanGenuchtenCapillaryPressure > Parameters

# Parameters
The capillary pressure constitutive model is listed in the 
`<Constitutive>` block of the input XML file.
The capillary pressure model must be assigned a unique name via
`name` attribute.
This name is used to assign the model to regions of the physical
domain via a `materialList` attribute of the `<ElementRegions>`
node.

The following attributes are supported:



Below are some comments on the model parameters:

* `phaseNames` - The number of phases can be either 2 or 3. The phase names entered for this attribute should match the phase names specified in the relative permeability block, either in :doc:`/coreComponents/constitutive/docs/BrooksCoreyRelativePermeability` or in :doc:`/coreComponents/constitutive/docs/ThreePhaseRelativePermeability`. The capillary model assumes that oil is always present. Supported phase names are:

===== ===========
Value Phase
===== ===========
oil   Oil phase
gas   Gas phase
water Water phase
===== ===========

* `phaseMinVolFraction` - The list of minimum volume fractions :math:`S_{\ell,min}` for each phase is specified in the same order as in `phaseNames`. Below this volume fraction, the phase is assumed to be immobile. The values entered for this attribute have to match those of the same attribute in the relative permeability block.

* `phaseCapPressureExponentInv` - The list of exponents :math:`m_{\ell}` for each phase is specified in the same order as in `phaseNames`. The parameter corresponding to the oil phase is not used.

* `phaseCapPressureMultiplier` - The list of multipliers :math:`\alpha_{\ell}` for each phase is specified in the same order as in `phaseNames`. The parameter corresponding to the oil phase is not used.

* `capPressureEpsilon` - The parameter :math:`\epsilon`. This parameter is used for both the water-phase and gas-phase capillary pressure. To avoid extremely large, or infinite, capillary pressure values, we set :math:`P_{c,w}(S_w) := P_{c,w}(\epsilon)` whenever :math:`S_w < \epsilon`. The gas-phase capillary pressure is treated analogously.
