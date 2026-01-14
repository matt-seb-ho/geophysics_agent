**Context:** Linearalgebra > DofManager > Brief description

# Brief description
The main aim of the Degrees-of-Freedom (DoF) Manager class is to handle all
degrees of freedom associated with fields that exist on mesh elements, faces, edges and nodes.
It creates a map between local mesh objects and global DoF indices.
Additionally, DofManager simplifies construction of system matrix sparsity patterns.

Key concepts are locations and connectors.
Locations, that can be elements, faces, edges or nodes, represent where the DoF is assigned.
For example, a DoF for pressure in a two-point flux approximation will be on a cell (i.e. element), while a displacement DoF for structural equations will be on a node.
The counterparts of locations are connectors, that are the geometrical entities
that link together different DoFs that create the sparsity pattern.
Connectors can be elements, faces, edges, nodes or none.
Using the same example as before, connectors will be faces and cells, respectively.
The case of a mass matrix, where every element is linked only to itself, is an example when there are no connectors, i.e. these have to be set to none.

DoFs located on a mesh object are owned by the same rank that owns the object in parallel mesh partitioning.
Two types of DoF numbering are supported, with the difference only showing in parallel runs of multi-field problems.

  * Initially, each field is assigned an independent DoF numbering that starts at 0 and is contiguous across all MPI ranks.
    Within each rank, locally owned DoFs are numbered sequentially across mesh locations, and within each mesh location (e.g. node) - sequentially according to component number.
    With this numbering, sparsity patterns can be constructed for individual sub-matrices that represent diagonal/off-diagonal blocks of the global coupled system matrix.

  * After all fields have been declared, the user can call `DofManager::reorderByRank()`, which constructs a globally contiguous DoF numbering across all fields.
    Specifically, all DoFs owned by rank 0 are numbered field-by-field starting from 0, then those on rank 1, etc.
    This makes global system sparsity pattern compatible with linear algebra packages that only support contiguous matrix rows on each rank.
    At this point, coupled system matrix sparsity pattern can be constructed.

Thus, each instance of `DofManager` only supports one type of numbering.
If both types are required, the user is advised to maintain two separate instances of `DofManager`.


`DofManager` allocates a separate "DOF index" array for each field on the mesh.
It is an array of global indices, where each value represents the first DoF index for that field and location (or equivalently, the row and column offset of that location's equations and variables for the field in the matrix).
For example, if index array for a field with 3 components contains the value N, global DoF numbers for that location will be N, N+1, N+2.
DoF on ghosted locations have the same indices as on the owning rank.
The array is stored under a generated key, which can be queried from the DoF manager, and is typically used in system assembly.
