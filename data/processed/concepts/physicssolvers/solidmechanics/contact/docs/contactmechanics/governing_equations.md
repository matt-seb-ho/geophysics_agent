**Context:** Physicssolvers > Solidmechanics > Contact > ContactMechanics > Governing Equations

## Governing Equations
GEOS contact solvers solve the the balance of linear momentum within a fractured solid, accounting for the continuity of stress across surfaces (i.e., fractures), i.e.

.. math```
   \nabla \cdot \sigma = 0 \\\\
   [[\sigma]] \cdot \mathbf{n} = 0

Where:

* :math:`\sigma` is the stress tensor in the solid,
* :math:`\mathbf{n}` is the outward unit normal to the surface,
* :math:`[[\sigma]]` is the stress jump across the surface.

On each fracture surface, a no-interpenetration constraint is enforced. Additionally, tangential tractions can also be generated, which are modeled using a regularized Coulomb model to describe frictional sliding.
