**Context:** Developerguide > Keycomponents > WorkingWithData > Registering Intrinsic data on a Mesh Object

## Registering Intrinsic data on a Mesh Object
As mentioned above, `Intrinsic` data is typically a member of the mesh object,
and is registered in the constructor of the mesh Object.
Taking the `NodeManager` and the `referencePosition` as an example, we
point out that the reference position is actually a member in the
`NodeManager`.


   :language: c++
   :start-after: //START_SPHINX_REFPOS
   :end-before: //END_SPHINX_REFPOS

This member is registered in the constructor for the `NodeManager`.


   :language: c++
   :start-after: //START_SPHINX_REFPOS_REG
   :end-before: //END_SPHINX_REFPOS_REG

Finally in order to access this data, the `NodeManager` provides explicit
accessors.


   :language: c++
   :start-after: //START_SPHINX_REFPOS_ACCESS
   :end-before: //END_SPHINX_REFPOS_ACCESS

Thus the interface for `Intrinsic` data is set by the object that it is a part
of, and the developer may only access the data through the accesssors from
outside of the mesh object class scope.
