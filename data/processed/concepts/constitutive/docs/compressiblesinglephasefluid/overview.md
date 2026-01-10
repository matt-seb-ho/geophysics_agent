**Context:** Constitutive > CompressibleSinglePhaseFluid > Overview

# Overview
This model represents a compressible single-phase fluid with constant compressibility
and pressure-dependent viscosity.
These assumptions are valid for slightly compressible fluids, such as water, and some
types of oil with negligible amounts of dissolved gas.

Specifically, fluid density is computed as



where :math:`c_\rho` is compressibility, :math:`p_0` is reference pressure, :math:`\rho_0` is
density at reference pressure, :math:`\beta_f` is the fluid thermal expansion coefficient, :math:`T_0` is reference temperature.

Similarly,



where :math:`c_\mu` is viscosibility (viscosity compressibility), :math:`\mu_0` is reference viscosity.

Either exponent may be approximated by linear (default) or quadratic terms of Taylor series expansion.
Currently there is no temperature dependence in the model, although it may be added in future.
