**Context:** Physicssolvers > Multiphysics > Poromechanics > Governing Equations

## Governing Equations
In our model, the geomechanics (elasticity) equation is expressed in terms of the total stress :math:`\mathbf{\sigma}`:



where it relates to effective stress :math:`\mathbf{\sigma\prime}` and pore pressure :math:`p` through Biot's coefficient :math:`b`:



The fluid mass conservation equation is expressed in terms of pore pressure and volumetric (mean) total stress:



where :math:`M` is the Biot's modulus and :math:`K_{dr}` is the drained bulk modulus.

Unlike the conventional reservoir model that uses Lagranges porosity, in the coupled geomechanics and flow model, Eulers porosity :math:`\phi` is adopted so the porosity variation is derived as:



where :math:`K_{s}` is the bulk modulus of the solid grain and :math:`\epsilon_v` is the volumetric strain.

# Parameters
The poroelasticity model is implemented as a main solver listed in
`<Solvers>` block of the input XML file that calls both SolidMechanicsLagrangianFEM and SinglePhaseFlow solvers.
In the main solver, it requires the specification of solidSolverName, flowSolverName, and couplingTypeOption.

The following attributes are supported:



* `couplingTypeOption`: defines the coupling scheme.

The solid constitutive model used here is PoroLinearElasticIsotropic, which derives from ElasticIsotropic and includes an additional parameter: Biot's coefficient. The fluid constitutive model is the same as SinglePhaseFlow solver. For the parameter setup of each individual solver, please refer to the guideline of the specific solver.

An example of a valid XML block for the constitutive model is given here:


  :language: xml
  :start-after: <!-- SPHINX_POROELASTIC_CONSTITUTIVE -->
  :end-before: <!-- SPHINX_POROELASTIC_CONSTITUTIVE_END -->

# Example

  :language: xml
  :start-after: <!-- SPHINX_POROELASTIC_SOLVER -->
  :end-before: <!-- SPHINX_POROELASTIC_SOLVER_END -->
