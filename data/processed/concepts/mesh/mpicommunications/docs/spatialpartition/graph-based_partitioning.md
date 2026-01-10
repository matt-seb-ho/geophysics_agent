**Context:** Mesh > Mpicommunications > SpatialPartition > Graph-based partitioning

## Graph-based partitioning
The Graph-based partitioning is used only when importing exernal meshes using the `VTKMesh`
(see :ref:`TutorialFieldCase` section for more details using external meshes).
While importing themesh, `vtk` computes the graph of connectivity between all the volume elements of the mesh.
The partitioning is then done using whether a KD-tree or the PTSCOTCH_, METIS_, PARMETIS_ libraries.
The graph is not weighted so the expected result is as mesh divided in `n` parts,
with `n` being the number of MPI ranks used for simulation containing a similar amount of cells.

# Ghost ranks
Each object (node, edge, face, or cell) has a `ghost rank` attribute, stored in the `ghostRank` field. 
If a object does not appear in any other partition as a ghost, its ghost rank is a large negative number, -2.14e9 in a typical system.
If a object is real (owned by the current partition) but exists in other partitions as ghosts, its ghost rank is -1.
The ghost rank of a ghost object is the rank of the partition that owns the corresponding real object.

# Considerations for visualization
In VisIt, a partition is called a `domain`. 
The ID of a domain is the rank of the corresponding partition in GEOS plus one.
VisIt would display all elements/objects regardless if they are real or ghosts.
As information about a ghost is synchronized with the real object, VisIt just overlaying the same images on top of each other.
The user would not perceive the overlapping between partitions unless the models are shown as semi-transparent entities.
Note that if ghosts are not hidden, results from a `query` operation, such as summation of variable values, would be wrong due to double-counting.
Therefore, it is a good practice or habit to hide ghost objects using ghostRank as a filter. 

If the visualization method involves interpolation, such as interpolating a zonal field into a nodal field or generating contours, 
the interpretation near partition boundaries is not accurate.

.. _METIS: http://glaros.dtc.umn.edu/gkhome/metis/metis/overview
.. _PARMETIS: http://glaros.dtc.umn.edu/gkhome/metis/parmetis/overview
.. _PTSCOTCH: https://www.labri.fr/perso/pelegrin/scotch/