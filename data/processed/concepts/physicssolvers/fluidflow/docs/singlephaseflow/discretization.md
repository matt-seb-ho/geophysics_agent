**Context:** Physicssolvers > Fluidflow > SinglePhaseFlow > Discretization

## Discretization
### Space Discretization
Let :math:`\Omega \subset \mathbb{R}^n, \, n =1,2,3` be an open set defining the computational domain. We consider :math:`\Omega` meshed by element such that :math:`\Omega = \cup_{i}V_i` and integrate the single phase flow equation, described above, over each element :math:`V_i`:



Applying the divergence theorem to the second term leads to



where :math:`S_i` represents the surface area of the element :math:`V_i` and :math:`\boldsymbol{n}` is a outward unit vector normal to the surface.

For the flux term, the (static) transmissibility is currently computed with a Two-Point Flux Approximation (TPFA) as described in :ref:`FiniteVolume`.

The pressure-dependent mobility :math:`\lambda = \frac{\rho}{\mu}` at the interface is approximated using a first-order upwinding on the sign of the potential difference.

### Time Discretization
Let :math:`t_0 < t_1 < \cdots < t_N=T` be a grid discretization of the time interval :math:`[t_0,T], \, t_0, T \in \mathbb{R}^+`. We use the backward Euler (fully implicit) method to integrate the single phase flow equation between two grid points :math:`t_n` and :math:`t_{n+1}, \, n< N` to obtain the residual equation:



where :math:`\Delta t = t_{n+1}-t_n` is the time-step. The expression of this residual equation and its derivative are used to form a linear system, which is solved via the solver package.

# Parameters
The solver is enabled by adding a `<SinglePhaseFVM>` node in the Solvers section.
Like any solver, time stepping is driven by events, see :ref:`EventManager`.

The following attributes are supported:



In particular:

* `discretization` must point to a Finite Volume flux approximation scheme defined in the Numerical Methods section of the input file (see :ref:`FiniteVolume`)
* `fluidName` must point to a single phase fluid model defined in the Constitutive section of the input file (see :ref:`Constitutive`)
* `solidName` must point to a solid mechanics model defined in the Constitutive section of the input file (see :ref:`Constitutive`)
* `targetRegions` is used to specify the regions on which the solver is applied

Primary solution field label is `pressure`.
Initial conditions must be prescribed on this field in every region, and boundary conditions
must be prescribed on this field on cell or face sets of interest.


# Example

  :language: xml
  :start-after: <!-- SPHINX_TUT_INT_HEX_SOLVERS -->
  :end-before: <!-- SPHINX_TUT_INT_HEX_SOLVERS_END -->

We refer the reader to :ref:`this page <TutorialSinglePhaseFlowWithInternalMesh>` for a complete tutorial illustrating the use of this solver.
