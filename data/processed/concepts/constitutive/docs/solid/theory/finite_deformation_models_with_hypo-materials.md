**Context:** Constitutive > Solid > Theory > Finite Deformation Models with Hypo-Materials

## Finite Deformation Models with Hypo-Materials
In the finite deformation regime, there are two broad classes of constitutive models frequently used:

- Hypo-elastic models (and inelastic extensions)
- Hyper-elastic models (and inelastic extensions)

Hypo-materials typically rely on a rate-form of the constitutive equations expressed in the spatial configuration.  
Let :math:[\bm{v}(\bm{x},t)` denote the spatial velocity field.  It can be decomposed into symmetric and anti-symmetric
components as


   \bm{w} = \frac{1}{2} \left( \nabla \bm{v} - \bm{v} \nabla \right ),

where :math:`\bm{d}` is the deformation rate tensor and :math:`\bm{w}` is the spin tensor. 
A hypo-material model can be written in rate form as



where :math:`\mathring{\bm{\tau}}` is an `objective rate ](https://en.wikipedia.org/wiki/Objective_stress_rate) of the Kirchoff stress 
tensor, :math:[\bm{c}` is the tangent stiffness tensor, 
and :math:`\bm{d}^e` is the elastic component of the deformation rate.
We see that the structure is similar to the rate form in the small strain regime, 
except the rate of Cauchy stress is replaced with an objective rate of Kirchoff stress, 
and the linearized strain rate is replaced with the deformation rate tensor.  
 
The key difference separating most hypo-models is the choice of the objective stress rate. 
In GEOS, we adopt the incrementally objective integration algorithm proposed by 
`Hughes and Winget (1980) ](https://onlinelibrary.wiley.com/doi/abs/10.1002/nme.1620151210)_.
This method relies on the concept of an incrementally rotating frame of reference in order
to preserve objectivity of the stress rate. In particular, the stress update sequence is

.. math```
      \Delta{\tensor{R}} = ( \tensor{I} - \frac{1}{2} \Delta t {\tensor{w}} )^{-1} ( \tensor{I} + \frac{1}{2} \Delta t {\tensor{w}} )
      &\qquad \text{(compute incremental rotation)}, \\
      \tensor{\bar{\tau}}^{n} = \Delta{\tensor{R}} \tensor{\tau}^{n} \Delta{\tensor{R}}^T
      &\qquad \text{(rotate previous stress)}, \\
      \tensor{\tau}^{n+1} = \tensor{\bar{\tau}}^{n} + \Delta \tensor{\tau}
      &\qquad \text{(call constitutive model to update stress)}.

First, the previous timestep stress is rotated to reflect any rigid rotations occuring over the timestep.
If the model has tensor-valued state variables besides stress, these must also be rotated.
Then, a standard constitutive update routine can be called, typically driven by the incremental 
strain :math:`\Delta \bm{\epsilon} = \Delta t \bm{d}`.
In fact, an identical update routine as used for small strain models can be re-used at this point.


   deficiencies.  Most notably, the energy dissipation in a closed loading cycle of a hypo-elastic 
   material is not guaranteed to be zero, as one might desire from thermodynamic considerations.  
