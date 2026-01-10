**Context:** Physicssolvers > Fluidflow > ProppantTransport > Parameters

# Parameters
The solver is enabled by adding a `<ProppantTransport>` node
and a `<SurfaceGenerator>` node in the Solvers section.
Like any solver, time stepping is driven by events, see :ref:`EventManager`.

The following attributes are supported:



In particular:

* `discretization` must point to a Finite Volume flux approximation scheme defined in the Numerical Methods section of the input file (see :ref:`FiniteVolume`)
* `proppantName` must point to a particle fluid model defined in the Constitutive section of the input file (see :ref:`Constitutive`)
* `fluidName` must point to a slurry fluid model defined in the Constitutive section of the input file (see :ref:`Constitutive`)
* `solidName` must point to a solid mechanics model defined in the Constitutive section of the input file (see :ref:`Constitutive`)
* `targetRegions` attribute is currently not supported, the solver is always applied to all regions.

Primary solution field labels are `proppantConcentration` and
`pressure`.
Initial conditions must be prescribed on these field in every region, and boundary conditions
must be prescribed on these fields on cell or face sets of interest. For static (non-propagating) fracture problems, the fields `ruptureState` and
`elementAperture` should be provided in the initial conditions.

In addition, the solver declares a scalar field named `referencePorosity` and a vector field
named `permeability`, that contains principal values of the symmetric rank-2 permeability tensor
(tensor axis are assumed aligned with the global coordinate system).
These fields must be populated via :ref:`XML_FieldSpecification` section and `permeability` should
be supplied as the value of `coefficientName` attribute of the flux approximation scheme used.
