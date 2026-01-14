**Context:** Constitutive > Solid > ElasticIsotropicPressureDependent > Overview

# Overview
This model may be used for solid materials with a pressure-dependent elastic isotropic behavior.
The relationship between stress and strain is given by a [hyperelastic law ](https://en.wikipedia.org/wiki/Hyperelastic_material)_. The elastic constitutive equations for the volumetric and deviatoric stresses and strain are expressed as:


   
where :math:`p` and  :math:`q` are the volumetric and deviatoric components of the Cauchy stress tensor.
:math:`\epsilon_{v}^e` and :math:`\epsilon_{s}^e` are the volumetric and deviatoric components of the strain tensor. :math:`\epsilon_{v0}` and :math:`p_0` are the initial volumetric strain and initial pressure. :math:`C_r` denotes the elastic compressibility index,
and :math:`\mu` is the elastic shear modulus. In this model, the shear modulus is constant and the bulk modulus, :math:`K`, varies linearly with pressure as follows: 


