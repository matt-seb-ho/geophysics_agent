**Context:** Constitutive > Solid > Theory > Small Strain Models

## Small Strain Models
Let :math:[\bm{u}` denote the displacement field, and :math:`\nabla \bm{u}` its gradient. 
In small strain theory, ones assumes the displacement gradients :math:`\nabla \bm{u} \ll 1`.
In this case, it is sufficient to use the linearized strain tensor

.. math``
  \bm{\epsilon} = \frac{1}{2} \left( \nabla \bm{u} + \bm{u} \nabla \right )

as the deformation measure. Higher-order terms present in finite strain theories are neglected.
For inelastic problems, this strain is additively decomposed into elastic and inelastic components as

.. math``
  \bm{\epsilon} = \bm{\epsilon}^e + \bm{\epsilon}^{i}.

Inelastic strains can arise from a number of sources: plasticity, damage, etc.
Most constitutive models (including nonlinear elastic and inelastic models) can then be generically
expressed in rate form as

.. math```
  \dot{\bm{\sigma}} = \bm{c} : \dot{\bm{\epsilon}}^e

where :math:`\dot{\bm{\sigma}}` is the Cauchy stress rate and :math:`\bm{c}` is the tangent stiffness 
tensor.  Observe that the stress rate is driven by the elastic component :math:`\dot{\bm{\epsilon}}^e` of the strain rate.

In the time-discrete setting (as implemented in the code) the incremental constitutive update 
for stress is computed from a solid model update routine as



where :math:`\Delta \bm{\epsilon} = \bm{\epsilon}^{n+1}-\bm{\epsilon}^n` is the incremental strain, 
:math:`\Delta t` is the timestep size (important for rate-dependent models), and
:math:`Q^n` is a collection of material state variables (which may include the previous stress and
strain).

For path and rate independent models, such as linear elasticity,
a simpler constitutive update may be formulated in terms of the total strain:



GEOS will use this latter form in specific, highly-optimized solvers when we know in advance that a
linear elastic model is being applied.  The more general interface is
the default, however, as it can accommodate a much wider range of constitutive behavior within a common
interface.

When implicit timestepping is used, the solid models must also provide the stiffness tensor,



in order to accurately linearize the governing equations.
In many works, this fourth-order tensor is referred to as the algorithmic or consistent tangent, in the
sense that it must be "consistent" with the discrete timestepping scheme being used
(`Simo and Hughes 1987 ](https://doi.org/10.1016/0045-7825(85)90070-2)).  
For inelastic models, it depends not only on the intrinsic material stiffness, but also the incremental nature of the loading process.
The correct calculation of this stiffness can have a dramatic impact on the convergence rate of Newton-type
solvers used in the implicit solid mechanics solvers.

.. _DeformationTheory_Hypo:
