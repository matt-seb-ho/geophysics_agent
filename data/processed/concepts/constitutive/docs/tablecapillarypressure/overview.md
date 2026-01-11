**Context:** Constitutive > TableCapillaryPressure > Overview

# Overview
The user can specify the capillary pressures using tables describing a piecewise-linear capillary pressure function of volume fraction (i.e., saturation) for each phase, except the reference phase for which capillary pressure is assumed to be zero.
Depending on the number of fluid phases, this model is used as follows:

* For two-phase flow, the user must specify one capillary pressure table. During the simulation, the capillary pressure of the non-reference phase is computed by interpolating in the table as a function of the non-reference phase saturation.   

* For three-phase flow, the user must specify two capillary pressure tables. One capillary pressure table is required for the pair wetting-phase--intermediate-phase (typically, water-oil), and one capillary pressure table is required for the pair non-wetting-phase--intermediate-phase (typically, gas-oil). During the simulation, the former is used to compute the wetting-phase capillary pressure as a function of the wetting-phase volume fraction and the latter is used to compute the non-wetting-phase capillary pressure as a function of the non-wetting-phase volume fraction. The intermediate phase is assumed to be the reference phase, and its capillary pressure is set to zero.    

Below is a table summarizing the choice of reference pressure for the various phase combinations:
  
============================ ================
Phases present in the model  Reference phase
============================ ================
oil, water, gas              Oil phase 
oil, water                   Oil phase
oil, gas                     Oil phase
water, gas                   Gas phase
============================ ================

In all cases, the user-provided capillary pressure is used in GEOS to compute the phase pressure using the formula:



where :math:`p_{nw}` and :math:`p_w` are respectively the non-wetting-phase and wetting-phase pressures.    
  