**Context:** Datarepository > MappedVector > Element access

## Element access
`MappedVector` provides three main types of data access using `[]` operator:

* **Index lookup** is the fastest way of element random access if the ordinal index is known.

* **Key lookup** is similar to key lookup of any associative container and incurs similar cost.

* **KeyIndex lookup** uses a special type, `KeyIndex`, that contains both a key and an index.
  Initially the index is unknown and the key is used for the lookup.
  The `KeyIndex` is modified during lookup, storing the index located.
  If the user persists the `KeyIndex` object, they may reuse it in subsequent accesses and get the benefit of direct index access.

In addition to these, an STL-conformant iterator interface is available via `begin()` and `end()` methods.
The type iterated over is a key-pointer pair (provided as `value_type` alias).
