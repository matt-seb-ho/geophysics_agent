**Context:** Constitutive > Solid > Theory > Introduction

## Introduction
The solid mechanics solvers in GEOS work in a time-discrete setting, in which the system state
at time :math:[t^n` is fully known, and the goal of the solution procedure is to advance forward 
one timestep to :math:`t^{n+1} = t^n + \Delta t`.  
As part of this process, calls to a 
solid model must be made to compute the updated stress :math:`\bm{\sigma}^{n+1}` resulting from 
incremental deformation over the timestep.  
History-dependent models may also need to compute updates to one or more internal state 
variables :math:`Q^{n+1}`.

The exact nature of the incremental update will depend, however, on the kinematic
assumptions made. 
Appropriate measures of deformation and stress depend on assumptions of
`infinitesimal ](https://en.wikipedia.org/wiki/Infinitesimal_strain_theory) or 
[finite ](https://en.wikipedia.org/wiki/Finite_strain_theory) 
strain, as well as other factors like rate-dependence and material anisotropy.

This section briefly reviews three main classes of solid models in GEOS, grouped by their kinematic assumptions. 
The presentation is deliberately brief, as much more extensive presentations can be 
found in almost any textbook on linear and nonlinear solid mechanics.

