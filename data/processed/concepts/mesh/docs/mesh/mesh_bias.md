**Context:** Mesh > Mesh > Mesh Bias

# Mesh Bias
The internal mesh generator is capable of producing meshes with element sizes that vary smoothly over space.
This is achieved by specifying `xBias`, `yBias`, and/or `zBias` fields.
(Note: if present, the length of these must match `nx`, `ny`, and `nz`, respectively, and each individual value must be in the range (-1, 1).)

For a given element block, the average element size will be



the element on the left-most side of the block will have size



and the element on the right-most side will have size




The following are the two most common scenarios that occur while designing a mesh with bias:

1. The size of the block and the element size on an adjacent region are known.  Assuming that we are to the left of the target block, the appropriate bias would be:



2. The bias of the block and the element size on an adjacent region are known.  Again, assuming that we are to the left of the target block, the appropriate size for the block would be:




The following is an example of a mesh block along each dimension, and an image showing the corresponding mesh.  Note that there is a core region of elements with zero bias, and that the transitions between element blocks are smooth.


  :language: xml
  :start-after: <!-- SPHINX_MESH_BIAS -->
  :end-before: <!-- SPHINX_MESH_BIAS_END -->



