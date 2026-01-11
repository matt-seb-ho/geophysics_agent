**Context:** Linearalgebra > DofManager > Example

# Example
Here we show how the sparsity pattern is computed for a simple 2D quadrilateral mesh with 6 elements.
Unknowns are pressure, located on the element center, and displacements (*x* and *y* components), located on the nodes.
For fluxes, a two-point flux approximation (TPFA) is used.
The representation of the sparsity pattern of the :math:`\mathsf{C_L}` matrix (connectors/locations) for the simple mesh, shown in :numref:`meshDofManagerFig`, is
reported in :numref:`CLDofManagerFig`.
It can be noticed that the two unknowns for the displacements *x* and *y* are grouped together.
Elements are the connectivity for DoF on nodes (Finite Element Method for displacements) and on elements (pressures).
Faces are the connectivity for DoF on elements (Finite Volume Method for pressure), being the flux computation based on the pressure on the two adjacent elements.

.. _meshDofManagerFig:

   :align: center
   :width: 250
   :figclass: align-center

   Small 2D quadrilateral mesh used for this examples.
   Nodes are label with black numbers, elements with light gray numbers and
   faces with italic dark gray numbers.

.. _CLDofManagerFig:

   :align: center
   :width: 500
   :figclass: align-center

   Sparsity pattern of the binary matrix connections/locations.

The global sparsity pattern, shown in :numref:`patternDofManagerFig`, is obtained through the symbolic multiplication of the transpose of the matrix :math:`\mathsf{C_L}` and the matrix itself, i.e. :math:`\mathsf{P = C_L^T C_L}`.

.. _patternDofManagerFig:

   :align: center
   :width: 400
   :figclass: align-center

   Sparsity pattern of the global matrix, where red and green entries are related to the displacement field and to the pressure field, respectively.
   Blue entries represent coupling blocks.
