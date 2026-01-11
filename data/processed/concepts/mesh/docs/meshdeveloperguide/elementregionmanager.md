**Context:** Mesh > meshDeveloperGuide > ElementRegionManager

## ElementRegionManager
The element data structure is significantly more complicated than the other Managers.
While the other managers are "flat" across the `MeshLevel`, the element data structure seeks to provide
a hierarchy in order to define groupings of the physical problem, as well as collecting discretization of
similar topology.
At the top of the element branch of the hierarchy is the `ElementRegionManager`.
The `ElementRegionManager` holds a collection of instantiations of `ElementRegionBase` derived
classes.

#### ElementRegion
Conceptually the `ElementRegion` are used to defined regions of the problem domain where a
`PhysicsSolver` will be applied.

- The `CellElementRegion` is related to all the polyhedra
- The `FaceElementRegion` is related to all the faces that have physical meaning in the
  domain, such as fractures and faults. This object should not be mistaken with the
  `FaceManager`. The `FaceManager` handles all the faces of the mesh, not only the
  faces of interest.
- The `WellElementRegion` is related to the well geometry.

An `ElementRegion` also has a list of materials allocated at each quadrature point across the entire
region.
One example of the utility of the `ElementRegion` is the case of the simulation of the mechanics
and flow within subsurface reservoir with an overburden.
We could choose to have two `ElementRegion`, one being the reservoir, and one for the
overburden.
The mechanics solver would be applied to the entire problem, while the flow problem would be applied only
to the reservoir region.

Each `ElementRegion` holds some number of `ElementSubRegion`.
The `ElementSubRegion` is meant to hold all the element topologies present in an `ElementSubRegion`
in their own groups.
For instance, for a `CellElementRegion`, there may be one `CellElementSubRegion` for all
tetrahedra, one for all hexahedra, one for all wedges and one for all the pyramids (:numref:`meshPolyMeshDevFig`).

.. _meshPolyMeshDevFig:

   :align: center
   :width: 500
   :figclass: align-center

   Model meshed with different cell types

Now that all the classes of the mesh hierarchy has been described, we propose to adapt the diagram
presented in :numref:`diagMeshDevFig` to match with the example presented in :numref:`modelMeshDevFig`.

Direct links to some useful class documentation:

`ObjectManagerBase API ](../../../doxygen_output/html/classgeos_1_1_object_manager_base.html)

[MeshLevel API ](../../../doxygen_output/html/classgeos_1_1_mesh_level.html)

[NodeManager API ](../../../doxygen_output/html/classgeos_1_1_node_manager.html)

[FaceManager API ](../../../doxygen_output/html/classgeos_1_1_face_manager.html)
