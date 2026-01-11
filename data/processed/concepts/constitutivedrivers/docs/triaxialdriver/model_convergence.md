**Context:** Constitutivedrivers > TriaxialDriver > Model Convergence

## Model Convergence
The last two columns of the output file contain information about the convergence behavior of the material driver.  In `triaxial` mode, the mixed nature of the stress/strain control requires using a Newton solver to converge the solution.  This last column reports the number of Newton iterations and final residual norm.  Large values here would be indicative of the material model struggling (or failing) to converge.  Convergence failures can result from several reasons, including:

1. Inappropriate material parameter settings
2. Overly large timesteps
3. Infeasible loading conditions (i.e. trying to load a material to a physically-unreachable stress point)
4. Poor model implementation

We generally spend a lot of time vetting the material model implementations (#4).  When you first encounter a problem, it is therefore good to explore the other three scenarios first.  If you find something unusual in the model implementation or are just really stuck, please submit an issue on our issue tracker so we can help resolve any bugs.
