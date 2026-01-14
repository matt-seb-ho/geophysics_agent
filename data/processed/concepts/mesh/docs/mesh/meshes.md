**Context:** Mesh > Mesh > Meshes

# Meshes
The purpose of this document is to explain how users and developers interact with mesh data.
This section describes how meshes are handled and stored in GEOS.

There are two possible methods for generating a mesh:
either by using GEOS's internal mesh generator (for Cartesian meshes only),
or by importing meshes from various common mesh file formats.
This latter options allows one to work with more complex geometries,
such as unstructured meshes comprised of a variety of element types (polyhedral elements).


  This convention affects mesh topology, and finite element / volume computations. 

************************
Internal Mesh Generation
************************
