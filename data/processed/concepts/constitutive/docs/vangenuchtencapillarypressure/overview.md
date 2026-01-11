**Context:** Constitutive > VanGenuchtenCapillaryPressure > Overview

# Overview
In GEOS, the oil-phase pressure is assumed to be the primary
pressure.
The following paragraphs explain how the
Van Genuchten capillary pressure model
is used to compute the water-phase and gas-phase
pressures as:



and




The Van Genuchten model computes the water-phase capillary
pressure as a function of the water-phase volume fraction as:

.. math``
  P_c(S_w) = \alpha_w  ( S_{w,scaled}^{-1/m_w} - 1 )^{ (1-m_w)/2 },

where the scaled water-phase volume fraction is computed as:

.. math``
   S_{\textit{w,scaled}} = \frac{S_w - S_{\textit{w,min}} }{1 - S_{\textit{w,min}} - S_{\textit{o,min}} - S_{\textit{g,min} }}.

The gas-phase capillary pressure is computed analogously.
