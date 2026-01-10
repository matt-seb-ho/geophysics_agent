**Context:** Constitutive > PorousSolids > Overview

# Overview
Simulation of fluid flow in porous media and of poromechanics,
requires to define, along with fluid properties, the hydrodynamical properties of
the solid matrix. Thus, for porous media flow and and poromecanical simulation in GEOS,
two types of composite constitutive models can be defined to specify the characteristics
of a porous material: (1) a `CompressibleSolid` model, used for flow-only simulations and which
assumes that all poromechanical effects can be represented by the pressure dependency of the
porosity; (2) a `PorousSolid` model which, instead, allows to couple any solid model with
a `BiotPorosity` model and to include permeability's dependence on the mechanical response.


Both these composite  models require the names of the solid, porosity and permeability models
that, combined, define the porous material. The following sections outline how these models can be
defined in the Constitutive block of the xml input files and which type of submodels they
allow for.
