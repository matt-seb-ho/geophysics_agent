**Context:** Mesh > Mesh > Basic Example

# Basic Example
The Internal Mesh Generator allows one to quickly build simple cartesian grids and divide
them into several regions.  The following attributes are supported in the input block for InternalMesh:




The following is an example XML `<mesh>` block, which will generate a vertical beam with two `CellBlocks` (one in red and one in blue in the following picture).

``xml
  <Mesh>
    <InternalMesh name="mesh"
                  elementTypes="{ C3D8 }"
                  xCoords="{ 0, 1 }"
                  yCoords="{ 0, 1 }"
                  zCoords="{ 0, 2, 6 }"
                  nx="{ 1 }"
                  ny="{ 1 }"
                  nz="{ 2, 4 }"
                  cellBlockNames="{ cb1, cb2 }"/>
  </Mesh>

- `name` the name of the mesh body
- `elementTypes` the type of the elements that will be generated.
- `xCoord` List of `x` coordinates of the boundaries of the `CellBlocks`
- `yCoord` List of `y` coordinates of the boundaries of the `CellBlocks`
- `zCoord` List of `z` coordinates of the boundaries of the `CellBlocks`
- `nx` List containing the number of cells in `x` direction within the `CellBlocks`
- `ny` List containing the number of cells in `y` direction within the `CellBlocks`
- `nz` List containing the number of cells in `z` direction within the `CellBlocks`
- `cellBlockNames` List containing the names of the `CellBlocks`




.. _Mesh_bias:
