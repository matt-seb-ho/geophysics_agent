**Context:** Tutorials > Step04 > Tutorial > Discretized computational domain

## Discretized computational domain
The following mesh is used in this tutorial:


   :width: 400px

This mesh contains 80 x 8 x 4 eight-node brick elements in the x, y and z directions, respectively.
Here, the `InternalMesh`
is used to generate a structured three-dimensional mesh with `C3D8` as
the `elementTypes`. This mesh is defined as a cell block with the name
`cb1`.


  :language: xml
  :start-after: <!-- SPHINX_BeamBendingMesh -->
  :end-before:  <!-- SPHINX_BeamBendingMeshEnd -->

------------------------------------