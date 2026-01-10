**Context:** Datarepository > MappedVector > Description

## Description
The container stores pointers to objects (which are themselves heap-allocated).
Each element may be optionally *owned* by the container, in which case it will be deleted upon removal or container destruction.
The pointers are stored in a contiguous memory allocation, and thus are accessible through an integral index lookup.
In addition, there is a map that provides a key lookup capability to the container if that is the preferred interface.

The container template has four type parameters:

* `T` is the object type pointed to by container entries

* `T_PTR` is a pointer-to-`T` type which must be either `T *` (default) or `std::unique_ptr<T>[

* `KEY_TYPE` is the type of key used in associative lookup

* `INDEX_TYPE` is the type used in index lookup
