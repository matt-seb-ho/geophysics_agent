**Context:** Constitutive > Solid > Plasticity > Two-Invariant Models

## Two-Invariant Models 
Two-invariant plasticity models use the first invariant of the Cauchy stress tensor and the second invariant of the deviatoric stress tensor to describe the yield surface. 

Here we use the following stress invariants to define the yield surface:  the von Mises stress :math:`q = \sqrt{3J_2} = \sqrt{3/2} \|\boldsymbol{s}\|` and mean normal stress :math:`p = I_1/3`. Here, :math:`I_1` and :math:`J_2` are the first invariant of the stress tensor and second invariant of the deviatoric stress, defined as



in which :math:`\boldsymbol{1}` is the identity tensor. 

Similarly, we can define invariants of strain tensor, namely, volumetric strain :math:`\epsilon_v` and deviatoric strain :math:`\epsilon_s`.



Stress and strain tensors can then be recomposed from the invariants as:





in which :math:`\hat{\boldsymbol{n}} = \boldsymbol{e}/\|\boldsymbol{e}\|`.

The following two-invariant models are currently implemented in GEOS:

  - :ref:`DruckerPrager <DruckerPrager>`

  - :ref:`J2Plasticity <J2Plasticity>`

  - :ref:`ModifiedCamClay <ModifiedCamClay>`

  - :ref:`DelftEgg <DelftEgg>`
