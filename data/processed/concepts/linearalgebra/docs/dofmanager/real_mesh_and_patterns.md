**Context:** Linearalgebra > DofManager > Real mesh and patterns

# Real mesh and patterns
Now we build the pattern of the Jacobian matrix for a simple 3D mesh, shown in
:numref:`meshCubeDofManagerFig`. Fields are:

- displacement (location: node, connectivity: element) defined on the blue, orange and red regions;
- pressure (location: element, connectivity: face) defined on the green, orange and red regions;
- mass matrix (location: element, connectivity: element) defined on the green region only.

Moreover, following coupling are imposed:

- displacement-pressure (connectivity: element) on the orange region only;
- pressure-mass matrix and transpose (connectivity: element) everywhere it is
  possibile.

.. _meshCubeDofManagerFig:

   :align: center
   :width: 400
   :figclass: align-center

   Real mesh used to compute the Jacobian pattern.

:numref:`globalPatterDofManagerFig` shows the global pattern with the field-based ordering of unknowns.
Different colors mean different fields.
Red unkwnons are associated with displacement, yellow ones with pressure and blue ones with mass matrix.
Orange means the coupling among displacement and pressure, while green is the symmetric coupling among pressure and mass matrix.

.. _globalPatterDofManagerFig:

   :align: center
   :width: 400
   :figclass: align-center

   Global pattern with field-based ordering.
   Red is associated with displacement unknowns, yellow with pressure ones and blue with those of mass matrix field.
   Orange means the coupling among displacement and pressure, while green is the symmetric coupling among pressure and mass matrix.

:numref:`permutedPatterDofManagerFig` shows the global pattern with the MPI rank-based ordering of unknowns.
In this case, just two processes are used.
Again, different colors indicate different ranks.

.. _permutedPatterDofManagerFig:

   :align: center
   :width: 400
   :figclass: align-center

   Global pattern with MPI rank-based ordering.
   Red unkwnons are owned by rank 0 and green ones by rank 1.
   Blue indicates the coupling among the two processes.
