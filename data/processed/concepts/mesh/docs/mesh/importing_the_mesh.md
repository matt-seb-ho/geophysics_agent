**Context:** Mesh > Mesh > Importing the Mesh

# Importing the Mesh
Importing regions
*****************

Several blocks are involved to import an external mesh into GEOS, defined in the XML input file.
These are the `<Mesh>` block and the `<CellElementRegions>` block.

The mesh block has the following syntax:

``xml
  <Mesh>
    <VTKMesh
      name="MyMeshName"
      logLevel="1"
      file="/path/to/the/mesh/file.vtk"
      regionAttribute="myAttribute" />
  </Mesh>

..note::
  We advise users to use absolute path to the mesh file, and recommend the use of a [logLevel`
  of 1 or more to obtain some information about the mesh import, including the list of regions that
  are imported with their names, which is particularly useful to fill the field of the
  `CellElementRegions` block (see below). Some information about the imported surfaces is also provided.

GEOS uses `ElementRegions` to support different physics or to define different constitutive properties.
The `ElementRegions` block can contain several `CellElementRegion` blocks. A `CellElementRegion`
is defined as a set of cell-blocks, which are sets of elements with the same element
geometry, defined within the `cellBlocks` attribute.

The naming of cell-blocks depends on if the mesh contains a data array which has the
same value as the `regionAttribute` of the `VTKMesh` (which is `attribute` by default).
This attribute is used to define regions in the vtu file and assign the cells to a given region.

For now, loaded regions has the following limitations:
- The `regionAttribute` can only refer to integer values (no texts),
- Each element can belong to only one region.


   :align: center
   :width: 500

In GEOS, there are three different ways to select `cellBlocks` in a `CellElementRegion`:

- Using a list of the desired `regionAttribute` values.
  I.e. `"{ 1, 2 }"` selects all the cell-blocks of the `regionAttribute` 1 and 2.

- Using a list of the exact cell-blocks names from the mesh to contain in this CellElementRegion.
  I.e. `{ 1_tetrahedra, 1_pyramid, 1_hexahedra, 2_tetrahedra, 2_pyramid, 2_hexahedra }``

- Using a list of `fnmatch patterns ](https://metacpan.org/pod/File::FnMatch) to match cell-block names to add them in this `CellElementRegion`.
  I.e. `{ * }` selects every elements, `{ 1_* }` selects the `{ 1_tetrahedra, 1_pyramid, 1_hexahedra }` cell-blocks.

In the example presented above, the mesh is is composed of two regions. Each region contains 4 element types.

- If the vtu file contains an attribute equals to the `regionAttribute` of the `VTKMesh`,
  then all `cellBlock` are named with this convention: `regionAttribute_elementType`. Let's assume that
  the top region of the exemple above has `myAttribute` to 1, and that the bottom region has `myAttribute` to 2,

  * If we want the `CellElementRegion` to contain all the cells, we write:

  ..  code-block:: xml

    <!-- Method one: Use `*` to match all cellBlock names automatically. 
                     "{ [1-2]_* }" would have an equivalent result (range selection). -->
    <ElementRegions>
      <CellElementRegion
        name="MyRegion"
        cellBlocks="{ * }"
        materialList="{ water, rock }" />
    </ElementRegions>
    
    <!-- Method two: Use `1, 2` to target the mesh regions. -->
    <ElementRegions>
      <CellElementRegion
        name="MyRegion"
        cellBlocks="{ 1, 2 }"
        materialList="{ water, rock }" />
    </ElementRegions>

    <!-- Method three: manually name all cell-blocks. -->
    <ElementRegions>
      <CellElementRegion
        name="MyRegion"
        cellBlocks="{ 1_hexahedra, 1_wedges, 1_tetrahedra, 1_pyramids, 2_hexahedra, 2_wedges, 2_tetrahedra, 2_pyramids }"
        materialList="{ water, rock }" />
    </ElementRegions>

  * If we want two `CellElementRegion` with the top and bottom regions separated, we write:

  ```xml
    <!-- Method one: Use the `regionAttribute` to select region '1' in 'Top' region, and region '2' in 'Bot' region. -->
    <ElementRegions>
      <CellElementRegion
        name="Top"
        cellBlocks="{ 1 }"
        materialList="{ water, rock }"/>
      <CellElementRegion
        name="Bot"
        cellBlocks="{ 2 }"
        materialList="{ water, rock }" />
    </ElementRegions>

    <!-- Method two: Use `cellBlocks` for the same purpose, but by matching the name patterns. -->
    <ElementRegions>
      <CellElementRegion
        name="Top"
        cellBlocks="{ 1_* }"
        materialList="{ water, rock }"/>
      <CellElementRegion
        name="Bot"
        cellBlocks="{ 2_* }"
        materialList="{ water, rock }" />
    </ElementRegions>

    <!-- Method three: manually name the cell-blocks in the same regions. -->
    <ElementRegions>
      <CellElementRegion
        name="Top"
        cellBlocks="{ 1_hexahedra, 1_wedges, 1_tetrahedra, 1_pyramids }"
        materialList="{ water, rock }"/>
      <CellElementRegion
        name="Bot"
        cellBlocks="{ 2_hexahedra, 2_wedges, 2_tetrahedra, 2_pyramids }"
        materialList="{ water, rock }" />
    </ElementRegions>

- If the vtu file does not contain any region attribute field, then all the cells are grouped in a single
  region, and cellBlock names consist of just the cell types (hexahedra, wedges, tetrahedra, etc).
  Then in the exemple above, the `ElementRegions` can be defined as bellow:

```xml
  <!-- Method one: Use `*` to match all cellBlock names automatically.  -->
  <ElementRegions>
    <CellElementRegion
      name="MyRegion"
      cellBlocks="{ * }"
      materialList="{ water, rock }" />
  </ElementRegions>

  <!-- Exemple two: manually name the desired cell-blocks. -->
  <ElementRegions>
    <CellElementRegion
      name="MyRegion"
      cellBlocks="{ hexahedra, wedges, tetrahedra, pyramids }"
      materialList="{ water, rock }" />
  </ElementRegions>

  <!-- Exemple three: Use only the tetrahedric cell-blocks on this region (see the warning below) -->
  <ElementRegions>
    <CellElementRegion
      name="MyRegion"
      cellBlocks="{ tetrahedra }"
      materialList="{ water, rock }" />
  </ElementRegions>

.. warning[`
  **All** the imported `cellBlocks` must be included in one (and only one) of the `CellElementRegion`.
  Even if some cells are meant to be inactive during the simulation, they still have to be
  included in a `CellElementRegion` (this `CellElementRegion` should
  simply not be included as a targetRegion of any of the solvers involved in the simulation).

The `cellBlocks`` element types are :

- `hexahedra ](https://en.wikipedia.org/wiki/Hexahedron)
- [tetrahedra ](https://en.wikipedia.org/wiki/Tetrahedron)
- [wedges ](https://en.wikipedia.org/wiki/Triangular_prism)
- [pyramids ](https://en.wikipedia.org/wiki/Square_pyramid)
- [pentagonalPrisms ](https://en.wikipedia.org/wiki/Pentagonal_prism)
- [hexagonalPrisms ](https://en.wikipedia.org/wiki/Hexagonal_prism)
- [heptagonalPrisms ](https://en.wikipedia.org/wiki/Heptagonal_prism)
- [octagonalPrisms ](https://en.wikipedia.org/wiki/Octagonal_prism)
- [nonagonalPrisms ](https://en.wikipedia.org/wiki/Enneagonal_prism)
- [decagonalPrisms ](https://en.wikipedia.org/wiki/Decagonal_prism)
- [hendecagonalPrisms ](https://en.wikipedia.org/wiki/Hendecagonal_prism)
- [polyhedra ](https://en.wikipedia.org/wiki/Polyhedron)

An example of a `vtk` file with all the physical regions defined is used in :ref:`TutorialFieldCase`.

Importing surfaces
******************

Surfaces are imported through point sets in GEOS. This feature is only supported using the `vtk` file format.
In the same way than the regions, the surfaces of interests can be defined using the `physical entity names`.
The surfaces are automatically imported in GEOS if they exist in the `vtk` file.
Within GEOS, the point set will have the same name than the one given in the file. This name can be used
again to impose boundary condition.

For instance, if a surface is named "Bottom" and the user wants to
impose a Dirichlet boundary condition of 0 on it, it can be easily done using this syntax:

``xml
  <FieldSpecifications>
    <FieldSpecification
      name="zconstraint"
      objectPath="nodeManager"
      fieldName="Velocity"
      component="2"
      scale="0.0"
      setNames="{ Bottom }"/>
  </FieldSpecifications>

The name of the surface of interest appears under the keyword `setNames`. Again, an example of a `vtk`` file
with the surfaces fully defined is available within :ref:`TutorialFieldCase` or :ref:`ExampleIsothermalHystInjection`.

.. _VTK: https://vtk.org
