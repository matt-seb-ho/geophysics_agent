**Context:** Constitutive > BrooksCoreyRelativePermeability > Parameters

# Parameters
The relative permeability constitutive model is listed in the
`<Constitutive>` block of the input XML file.
The relative permeability model must be assigned a unique name via
`name` attribute.
This name is used to assign the model to regions of the physical
domain via a `materialList` attribute of the `<ElementRegions>`
node.

The following attributes are supported:



Below are some comments on the model parameters.

* `phaseNames` - The number of phases can be either two or three. Note that for three-phase flow, this model does not apply a special treatment to the intermediate phase relative permeability (no Stone or Baker interpolation). Supported phase names are:

===== ===========
Value Phase
===== ===========
oil   Oil phase
gas   Gas phase
water Water phase
===== ===========

* `phaseMinVolFraction` - The list of minimum volume fractions :math:`S_{\ell,min}` for each phase is specified in the same order as in `phaseNames`. Below this volume fraction, the phase is assumed to be immobile.

* `phaseRelPermExponent` - The list of exponents :math:`\lambda_{\ell}` for each phase is specified in the same order as in `phaseNames`.

* `phaseMaxValue` - The list of maximum values :math:`k_{\textit{r} \ell,\textit{max}}` for each phase is specified in the same order as in `phaseNames`.

