**Context:** Constitutive > TwoPhaseImmiscibleFluid > Overview

# Overview
This model represents a two-phase immiscible fluid with pressure-dependent density and viscosity.

For each phase, both density and viscosity are described as tabulated data, either in the form of `TableFunction` or text files.

In the case of text files, one file is expected per phase and should consist of three columns: pressure, density and viscosity.

Note that currently, there is no temperature dependence in the model.

