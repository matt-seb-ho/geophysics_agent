**Context:** Tutorials > Step02 > Tutorial > Externally Generated Tetrahedral Elements

## Externally Generated Tetrahedral Elements
In the second part of the tutorial, we discretize the
same cubic domain but with tetrahedral elements.
Tetrahedral meshes are not yet common in geomodeling
but offer tremendous flexibility
in modeling fracture planes, faults, complex reservoir
horizons and boundaries.
Just like for hexahedral meshes,
and for the same reasons (compatibility with finite volume and finite element methods),
tetrahedral meshes in GEOS must be conformal.


As stated previously, the problem we wish to solve here
is the exact same physical problem as with hexahedral grid blocks.
We apply a constant pressure condition (injection)
from the x=0 vertical face of the domain, and we let pressure
equilibrate over time. We observe the opposite side of the cube and expect
to see hydrostatic pressure profiles because of the gravitational effect.
The displacement is a single phase, compressible flow subject to gravity forces.
We use GEOS to compute the pressure inside each grid block.


The set-up for this problem is almost identical to
the hexahedral mesh set-up. We simply point our `Mesh` tag to
include a tetrahedral grid. The interest of not relying on I,J,K indices
for any property specification or well trajectory
makes it **easy to try different meshes for the same physical problems with GEOS**.
Swapping out meshes without requiring other modifications
to the input files makes mesh refinement studies easy to perform with GEOS.


Like before, the XML file for this problem is the following:

``console
   inputFiles/singlePhaseFlow/vtk/3D_10x10x10_compressible_tetra_gravity_smoke.xml


The only difference, is that now, the `Mesh` tag points GEOS to
a different mesh file called `cube_10x10x10_tet.vtk``.
This file contains nodes and tetrahedral elements in `vtk`_ format,
representing a different discretization of the exact same 10x10x10 cubic domain.


  :language: xml
  :start-after: <!-- SPHINX_TUT_EXT_TETRA_MESH -->
  :end-before: <!-- SPHINX_TUT_EXT_TETRA_MESH_END -->

The mesh now looks like this:


  :width: 400px


And the `vtk` file starts as follows (notice the tetrahedral point coordinates as real numbers):


   :caption: cube_10x10x10_tet.vtk
   :lines: 1-20

Again, the entire field is one region called `Domain` which contains `water` and `rock`.
Since we have imported a mesh with only one region, we can again set `cellBlocks` to `{ * }`
(we have could also set `cellBlocks` to `{ tetrahedra }` as the mesh has only tetrahedric cells).


  :language: xml
  :start-after: <!-- SPHINX_TUT_EXT_TETRA_ELEM_REGIONS -->
  :end-before: <!-- SPHINX_TUT_EXT_TETRA_ELEM_REGIONS_END -->

