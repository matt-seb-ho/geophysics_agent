**Context:** Mesh > Mesh > Supported Formats

# Supported Formats
GEOS provides features to run simulations on unstructured meshes.
It uses VTK_ to read the external meshes and its API to write
it into the GEOS mesh data structure.

The supported mesh elements for volume elements consist of the following:

- 4-node tetrahedra,
- 5-node pyramids,
- 6-node wedges,
- 8-node hexahedra,
- n-gonal prisms (n = 7, ..., 11).

The mesh can be divided in several regions.
These regions are intended to support different physics
or to define different constitutive properties.
By default, we use the `attribute` field to define the regions.

.. _ImportingExternalMesh:
