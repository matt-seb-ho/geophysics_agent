**Context:** Constitutive > Solid > Theory > Finite Deformation Models with Hyper-Materials

## Finite Deformation Models with Hyper-Materials
Hyper-elastic models (and inelastic extensions) attempt to correct the thermodynamic deficiencies of their hypo-elastic cousins.
The constitutive update can be generically expressed at



where :math:`\bm{S}` is the second Piola-Kirchoff stress and :math:`\Delta \mathbf{F}` is the incremental deformation gradient. 
Depending on the model, the deformation gradient can be converted to different deformation measures as needed.
Similarly, different stress tensors can be recovered through appropriate push-forward and pull-back operations.

In a hyperelastic material, the elastic response is 
expressed in terms of a stored strain-energy function that serves as the
potential for stress, e.g.



where :math:`\psi` is 
the stored energy potential, and :math:`\tensor{C}` is the right Cauchy-Green 
deformation tensor.  This potential guarantees that the energy dissipated or gained in a closed elastic cycle is zero.


