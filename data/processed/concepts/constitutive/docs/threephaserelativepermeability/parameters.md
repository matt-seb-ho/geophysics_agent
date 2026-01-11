**Context:** Constitutive > ThreePhaseRelativePermeability > Parameters

# Parameters
The relative permeability constitutive model is listed in the 
`<Constitutive>` block of the input XML file.
The relative permeability model must be assigned a unique name via
`name` attribute.
This name is used to assign the model to regions of the physical
domain via a `materialList` attribute of the `<ElementRegion>`
node.

The following attributes are supported:



Below are some comments on the model parameters.

* `phaseNames` - The number of phases should be 3. Supported phase names are:

===== ===========
Value Phase
===== ===========
oil   Oil phase
gas   Gas phase
water Water phase
===== ===========

* `phaseMinVolFraction` - The list of minimum volume fractions :math:`S_{\ell,min}` for each phase is specified in the same order as in `phaseNames`. Below this volume fraction, the phase is assumed to be immobile.

* `waterOilRelPermExponent` - The list of exponents :math:`\lambda_{\ell,wo}` for the two-phase water-oil relative permeability data, with the water exponent first and the oil exponent next. These exponents are then used to compute :math:`k_{r \ell,wo}` in the :doc:`/coreComponents/constitutive/docs/BrooksCoreyRelativePermeability`.

* `waterOilRelPermMaxValue` - The list of maximum values :math:`k_{\textit{r} \ell,wo,\textit{max}}` for the two-phase water-oil relative permeability data, with the water max value first and the oil max value next. These exponents are then used to compute :math:`k_{r \ell,wo}` in the :doc:`/coreComponents/constitutive/docs/BrooksCoreyRelativePermeability`.

* `gasOilRelPermExponent` - The list of exponents :math:`\lambda_{\ell,go}` for the two-phase gas-oil relative permeability data, with the gas exponent first and the oil exponent next. These exponents are then used to compute :math:`k_{r \ell,go}` in the :doc:`/coreComponents/constitutive/docs/BrooksCoreyRelativePermeability`.

* `gasOilRelPermMaxValue` - The list of maximum values :math:`k_{\textit{r} \ell,go,\textit{max}}` for the two-phase gas-oil relative permeability data, with the gas max value first and the oil max value next. These exponents are then used to compute :math:`k_{r \ell,go}` in the :doc:`/coreComponents/constitutive/docs/BrooksCoreyRelativePermeability`.
