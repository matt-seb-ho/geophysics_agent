**Context:** Physicssolvers > Solidmechanics > Contact > SolidMechanicsEmbeddedFractures > Discretization & soltuion strategy

# Discretization & soltuion strategy
The linear momentum balance equation is discretized using a low order finite element method. Moreover, to account for the influence of the fractures on the overall behavior, we utilize the enriched finite element method (EFEM)
with a piece-wise constant enrichment. This method employs an element-local enrichment of the FE space using the concept of assumedenhanced strain [1-6].

