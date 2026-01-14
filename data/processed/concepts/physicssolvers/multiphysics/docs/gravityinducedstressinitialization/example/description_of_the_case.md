**Context:** Physicssolvers > Multiphysics > Gravityinducedstressinitialization > Example > Description of the Case

## Description of the Case
We model the in-situ state of stress of a subsurface reservoir subject to a gravity-only induced stress and hydrostatic in-situ pressure condition. The domain is homogenous, isotropic and isothermal. The domain is subject to roller boundary conditions on lateral surfaces and at the base of the model, while the top of the model is a free surface.

.. _problemSketch1InitializationTest:

   :align: center
   :width: 300
   :figclass: align-center

   Sketch of the problem 


We set up and solve a PoroMechanics model to obtain the gradient of total stresses (principal stress components) across the domain due to gravity effects and hydrostatic pressure only. These numerical predictions are compared with the analytical solutions derived from `Eaton et al. (1969, 1975) ](https://onepetro.org/SPEATCE/proceedings/75FM/All-75FM/SPE-5544-MS/138715)_



For this example, we focus on the `Mesh`,
the `Constitutive`, and the `FieldSpecifications` tags.


------------------------------------------------------------------