**Context:** Tutorials > Step02 > Tutorial > Brief discussion about hexahedral meshes in GEOS

## Brief discussion about hexahedral meshes in GEOS
Although closely related, the hexahedral grids that GEOS
can process are slightly different
than either structured grid or corner-point grids.
The differences are worth pointing out here. In GEOS:

 - **Hexahedra can have irregular shapes**: no pillars are needed and
   vertices can be anywhere in space. This is useful for grids that turn, fold,
   or are heavily bent. Hexahedral blocks should nevertheless have 8 distinct
   vertices that are not coalesced.
   Some tolerance exists for degeneration to wedges
   in some solvers (finite element solvers), but it is best to avoid such situations
   and label elements according to their actual shape.
   Butterfly cells, flat cells, negative or zero volume cells will cause problems.
 - **The mesh needs to be conformal:** in 3D, this means that neighboring
   grid blocks have to share exactly a complete face. Note that corner-point
   grids do not have this requirement and neighboring blocks can be offset.
   When importing grids
   from commonly-used geomodeling packages, this is an important consideration. This
   problem is solved by splitting shifted grid blocks to restore conformity.
   While it may seem convenient to be able to have offset grid blocks at first,
   the advantages
   of conformal grids used in GEOS are worth the extra meshing effort:
   by using conformal grids,
   GEOS can run finite element and finite volume simulations on the same mesh
   without problems, going seamlessly from one numerical method to the other.
   This is key to enabling multiphysics simulation.
 - **There is no assumption of overall structure**: GEOS does not need to know
   a number of block in the X, Y, Z direction (no NX, NY, NZ) and does not assume that the
   mesh is a full cartesian domain that the interesting parts of the reservoir
   must be carved out from.
   Blocks are numbered by indices that assume
   nothing about spatial positioning and there is no concept of (i,j,k).
   This approach also implies that
   no "masks" are needed to remove inactive or dead cells, as often done
   in cartesian grids to get the actual reservoir contours from a bounding box,
   and here we only need to specify grid blocks that are active.
   For performance and flexibility, this lean approach to meshes is important.


