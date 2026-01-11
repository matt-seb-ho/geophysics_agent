**Context:** Tutorials > Step01 > Tutorial > Mesh

## Mesh
To solve this problem, we need to define a mesh for our numerical calculations.
This is the role of the **Mesh** element.

There are two approaches to specifying meshes in GEOS: internal or external.

  * The external approach allows to import mesh files created outside GEOS, such as a corner-point grid or an unstructured grid representing complex shapes and structures.
  * The internal approach uses GEOS's built-in capability to create simple meshes from a small number of parameters. It does not require any external file information. The geometric complexity of internal meshes is limited, but many practical problems can be solved on such simple grids.

In this tutorial, to keep things self-contained,
we use the internal mesh generator. We parameterize it with the **InternalMesh** element.


  :language: xml
  :start-after: <!-- SPHINX_TUT_INT_HEX_MESH -->
  :end-before: <!-- SPHINX_TUT_INT_HEX_MESH_END -->


**name**

Just like for solvers, we register the `InternalMesh` element using a unique **name** attribute.
Here the `InternalMesh` object is instantiated with the name `mesh`.


**elementTypes**


We specify the collection of elements types that this mesh contains.
Tetrahedra, hexahedra, and  wedges are examples of element types.
If a mesh contains different types of elements (a hybrid mesh),
we should indicate this here by listing all unique types of elements in curly brackets.
Keeping things simple, our element collection has only one type of element: a `C3D8` type representing a hexahedral element (linear 8-node brick).

A mesh can contain several geometrical types of elements.
For numerical convenience, elements are aggregated by types into `cellBlocks`.
Here, we only have linear 8-node brick elements, so the entire domain is one object called `cellBlock`.


**xCoords, yCoords, zCoords, nx, ny, nz**

This specifies the spatial arrangement of the mesh elements.
The mesh defined here goes from coordinate x=0 to x=10 in the x-direction, with `nx=10` subdivisions along this segment.
The same is true for the y-dimension and the z-dimension.
Our mesh is a cube of 10x10x10=1,000 elements with a bounding box defined by corner coordinates (0,0,0) and (10,10,10).






.. _Geometry_tag_single_phase_internal_mesh:

---------