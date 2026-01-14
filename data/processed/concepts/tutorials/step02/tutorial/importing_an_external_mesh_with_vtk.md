**Context:** Tutorials > Step02 > Tutorial > Importing an external mesh with VTK

## Importing an external mesh with VTK
In this first part of the tutorial, we use an hexahedral mesh provided to GEOS.
This hexahedral mesh is strictly identical to the grid used in the first tutorial (:ref:`TutorialSinglePhaseFlowWithInternalMesh`), but instead of using
the internal grid generator GEOS, we specify it with spatial node coordinates in `vtk` format.
To import external grid into GEOS, we did develop a component directly using the **vtk** library.


So here, our mesh consists of a simple sugar-cube stack of size 10x10x10.
We inject fluid from one vertical face of a cube (the face corresponding to x=0),
and we let the pressure equilibrate in the closed domain.
The displacement is a single-phase, compressible fluid subject to gravity forces,
so we expect the pressure to be constant on the injection face,
and to be close to hydrostatic on the opposite plane (x=10).
We use GEOS to compute the pressure inside each grid block over a period of time
of 100 seconds.



  :width: 400px

To see how to import such a mesh,
we inspect the following XML file:


``console
  inputFiles/singlePhaseFlow/vtk/3D_10x10x10_compressible_hex_gravity_smoke.xml


In the XML `Mesh` tag, instead of an `InternalMesh` tag,
we have a `VTKMesh` tag.
We see that a file called `cube_10x10x10_hex.vtk` is
imported using `vtk`, and this object is instantiated with a user-defined `name`` value.
The file here contains geometric information in `vtk ](https://vtk.org/)_ format
(it can also contain properties, as we will see in the next tutorial).


  :language: xml
  :start-after: <!-- SPHINX_TUT_EXT_HEX_MESH -->
  :end-before: <!-- SPHINX_TUT_EXT_HEX_MESH_END -->

Here is the `vtk` file :


   :caption: cube_10x10x10_hex.vtk
   :lines: 1-7

GEOS can run different physical solvers on different regions of the mesh at different times.
Here, to keep things simple, we run one solver (single-phase flow)
on the entire domain throughout the simulation.
To do so, we need to define a region encompassing the entire domain.
We will name it `Domain`, as refered to in the single-phase flow solver (in its `targetRegions`),
and list its constitutive models in the `materialList`, which are `water` and `rock`.
Since we have imported a mesh with only one region, we can set `cellBlocks` to `{ * }`
(we have could also set `cellBlocks` to `{ hexahedra }` as the mesh has only hexahedral cells).



  :language: xml
  :start-after: <!-- SPHINX_TUT_EXT_HEX_ELEM_REGIONS -->
  :end-before: <!-- SPHINX_TUT_EXT_HEX_ELEM_REGIONS_END -->



  changed and have not-hexahedral cells, GEOS will throw an error at the beginning of the
  simulation. See :ref:`Meshes` for more information.
