**Context:** Constitutive > Solid > ElasticOrthotropic > Overview

# Overview
This model may be used for solid materials with a linear elastic, orthotropic behavior.
This is most readily expressed in Voight notation as


      \sigma_{11} \\
      \sigma_{22} \\
      \sigma_{33} \\
      \sigma_{23} \\
      \sigma_{13} \\
      \sigma_{12}
    \end{bmatrix}
    =
    \begin{bmatrix}
      C_{11} & C_{12} &   C_{13} & 0 & 0 & 0 \\
      C_{12} & C_{22} &   C_{23} & 0 & 0 & 0 \\
      C_{13} & C_{23} &   C_{33} & 0 & 0 & 0 \\
      0 & 0 & 0 & C_{44} & 0 & 0 \\
      0 & 0 & 0 & 0 & C_{55} & 0 \\
      0 & 0 & 0 & 0 & 0 & C_{66}
    \end{bmatrix}
    \begin{bmatrix}
      \epsilon_{11} \\
      \epsilon_{22} \\
      \epsilon_{33} \\
      2\epsilon_{23} \\
      2\epsilon_{13} \\
      2\epsilon_{12}
    \end{bmatrix}.

This system contains nine independent constants.  These constants are calculated from the input parameters
indicated below.
