**Context:** Constitutive > BlackOilFluid > Dead oil

## Dead oil
In **dead-oil** each component occupies only one phase. Thus, the following partition matrix determines the components distribution within the
three phases:


    y_{gv} & y_{gl} & y_{ga}\\
    y_{ov} & y_{ol} & y_{oa}\\
    y_{wv} & y_{wl} & y_{wa}
    \end{bmatrix}
    = \begin{bmatrix}
    1 & 0 & 0 \\
    0  & 1 & 0 \\
    0 & 0 & 1
    \end{bmatrix}

and the phase densities are


      \rho_{v} = & \, \frac{\rho_{g}^{STC}}{B_{g}}.
