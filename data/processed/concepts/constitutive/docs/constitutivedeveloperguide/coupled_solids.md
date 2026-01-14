**Context:** Constitutive > constitutiveDeveloperGuide > Coupled Solids

## Coupled Solids
`CoupledSolid` models are employed to represent porous materials that require
both a mechanical behavior and constitutive laws that describe the
dependency of porosity and permeability on the primary unknowns.

The base class `CoupledSolidBase` implements some basic behaviors
and is used to access a generic `CoupledSolid` in a physics solver:


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_COUPLEDSOLID
   :end-before: //END_SPHINX_INCLUDE_COUPLEDSOLID

Additionally, a `template class` defines a base `CoupledSolid` model
templated on the types of solid, porosity, and permeability models:


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_00
   :end-before: //END_SPHINX_INCLUDE_00

While physics solvers that need a porous material only interface with a compound model,
this one has access to the standalone models needed:


    :language: c++
    :start-after: //START_SPHINX_INCLUDE_01
    :end-before: //END_SPHINX_INCLUDE_01

There are two specializations of a `CoupledSolid`:

- `CompressibleSolid`: this model is used whenever there is no need to define a full mechanical model,
  but only simple correlations that compute material properties (like porosity or permeability).
  This model assumes that the solid model is of type `NullModel` and is only templated on
  the types of porosity and permeability models.

- `PorousSolid`: this model is used to represent a full porous material where
  the porosity and permeability models need to be aware of the mechanical response of the material.
