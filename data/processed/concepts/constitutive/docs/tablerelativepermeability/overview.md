**Context:** Constitutive > TableRelativePermeability > Overview

# Overview
The user can specify the relative permeabilities using tables describing a piecewise-linear relative permeability function of volume fraction (i.e., saturation) for each phase.
Depending on the number of fluid phases, this model is used as follows:

* For two-phase flow, the user must specify two relative permeability tables, that is, one for the wetting-phase relative permeability, and one for the non-wetting phase relative permeability. During the simulation, the relative permeabilities are then obtained by interpolating in the tables as a function of phase volume fraction. 

* For three-phase flow, following standard reservoir simulation practice, the user must specify four relative permeability tables. Specifically, two relative permeability tables are required for the pair wetting-phase--intermediate phase (typically, water-oil), and two relative permeability tables are required for the pair non-wetting-phase--intermediate phase (typically, gas-oil). During the simulation, the relative permeabilities of the wetting and non-wetting phases are computed by interpolating in the tables as a function of their own phase volume fraction. The intermediate phase relative permeability is obtained by interpolating the two-phase relative permeabilities using the Baker interpolation procedure.  
  