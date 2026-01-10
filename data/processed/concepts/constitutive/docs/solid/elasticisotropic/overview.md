**Context:** Constitutive > Solid > ElasticIsotropic > Overview

# Overview
This model may be used for solid materials with a linear elastic isotropic behavior.
The relationship between stress and strain is given by [Hooke's Law ](https://en.wikipedia.org/wiki/Hooke%27s_law)_,
expressed as:



where :math:[\sigma_{ij}` is the :math:`ij` component of the Cauchy stress tensor,
:math:`\epsilon_{ij}` is the :math:`ij` component of the strain tensor,
:math:`\lambda` is the first Lamé elastic constant,
and :math:`\mu` is the elastic shear modulus.

Hooke's Law may also be expressed using `Voigt notation ](https://en.wikipedia.org/wiki/Voigt_notation)_ for stress and strain vectors as:



or,


      \sigma_{11} \\
      \sigma_{22} \\
      \sigma_{33} \\
      \sigma_{23} \\
      \sigma_{13} \\
      \sigma_{12}
    \end{bmatrix}
    =
    \begin{bmatrix}
      2\mu+\lambda  &   \lambda     &   \lambda   & 0   & 0 & 0 \\
          \lambda     &  2\mu+\lambda   &   \lambda   & 0   & 0 & 0 \\
          \lambda     &    \lambda    & 2\mu+\lambda & 0  & 0 & 0 \\
          0         &       0     &       0 &\mu  & 0 & 0 \\
      0         &           0     & 0       & 0   & \mu & 0 \\
      0         &       0     & 0       & 0   & 0 & \mu
    \end{bmatrix}
    \begin{bmatrix}
      \epsilon_{11} \\
      \epsilon_{22} \\
      \epsilon_{33} \\
      2\epsilon_{23} \\
      2\epsilon_{13} \\
      2\epsilon_{12}
    \end{bmatrix}.
