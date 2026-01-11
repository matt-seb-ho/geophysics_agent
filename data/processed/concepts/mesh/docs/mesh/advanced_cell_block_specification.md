**Context:** Mesh > Mesh > Advanced Cell Block Specification

# Advanced Cell Block Specification
It's possible to generate more complex `CellBlock` using the `InternalMeshGenerator`.
For instance, the staircase example is a model which is often used in GEOS as an integrated
test. It defines `CellBlocks` in the three directions to generate a staircase-like model
with the following code.

``xml
  <Mesh>
    <InternalMesh name="mesh1"
                  elementTypes="{C3D8}"
                  xCoords="{0, 5, 10}"
                  yCoords="{0, 5, 10}"
                  zCoords="{0, 2.5, 5, 7.5, 10}"
                  nx="{5, 5}"
                  ny="{5, 5}"
                  nz="{3, 3, 3, 3}"
                  cellBlockNames="{cb-0_0_0, cb-1_0_0, cb-0_1_0, cb-1_1_0,
                                   cb-0_0_1, cb-1_0_1, cb-0_1_1, cb-1_1_1,
                                   cb-0_0_2, cb-1_0_2, cb-0_1_2, cb-1_1_2,
                                   cb-0_0_3, cb-1_0_3, cb-0_1_3, cb-1_1_3}"/>
  </Mesh>

  <ElementRegions>
     <CellElementRegion name="Channel"
                    cellBlocks="{cb-1_0_0, cb-0_0_0, cb-0_0_1, cb-0_1_1, cb-0_1_2, cb-1_1_2, cb-1_1_3, cb-1_0_3}"
                    materialList="{fluid1, rock, relperm}"/>
     <CellElementRegion name="Barrier"
                    cellBlocks="{cb-0_1_0, cb-1_1_0, cb-1_1_1, cb-1_0_1, cb-1_0_2, cb-0_0_2, cb-0_0_3, cb-0_1_3}"
                    materialList="{}"/>
  </ElementRegions>

Thus, the generated mesh will be :


   :align: center
   :width: 500

Note that `CellBlocks` are ordered following the natural IJK logic, with indices increasing first in I (x-direction), then in J (y-direction) and last in K (z-direction).

.. _ExternalMeshUsage:

**************************
Using an External Mesh
**************************
