**Context:** Physicssolvers > Multiphysics > Gravityinducedstressinitialization > Example > Mesh

## Mesh
The following figure shows the mesh used for solving this poromechanical problem:

.. _problemSketch2InitializationTest:

   :align: center
   :width: 500
   :figclass: align-center

   Generated mesh 


The mesh was created with the internal mesh generator and parametrized in the `InternalMesh` XML tag. 
It contains 20x20x40 eight-node brick elements in the x, y, and z directions respectively. 
Such eight-node hexahedral elements are defined as `C3D8` elementTypes, and their collection forms a mesh
with one group of cell blocks named here `cellBlockNames`.



    :language: xml
    :start-after: <!-- SPHINX_MESH -->
    :end-before: <!-- SPHINX_MESH_END -->


------------------------