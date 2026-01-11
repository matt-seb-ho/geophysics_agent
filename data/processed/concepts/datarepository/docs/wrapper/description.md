**Context:** Datarepository > Wrapper > Description

## Description
In the filesystem analogy, a Wrapper may be thought of as a file that stores actual data.
Each `Wrapper` belong to a single `Group` much like a file belongs to a filesystem directory.
In general, more than one wrapper in the tree may refer to the same wrapped object, just like symlinks in the file system may refer to the same file.
However, only one wrapper should be *owning* the data (see below).

In the XML input file, `Wrapper` correspond to attribute of an XML element representing the containing `Group`.
See :ref:`XML_and_classes` for the relationship between XML input files and Data Repository.

`Wrapper<T>` is templated on the type of object it encapsulates, thus providing strong type safety when retrieving the objects.
As each `Wrapper` class instantiation will be a distinct type, Wrapper derives from a non-templated `WrapperBase` class that defines a common interface.
`WrapperBase` is the type of pointer that is stored in the `MappedVector` container within a `Group`.

`WrapperBase` provides several interface functions that delegate the work to the wrapped object if it supports the corresponding method signature.
This allows a collection of heterogeneous wrappers (i.e. over different types) to be treated uniformly.
Examples include:

* `size()`
* `resize(newSize)`
* `reserve(newCapacity)`
* `capacity()`
* `move(LvArray::MemorySpace)`

A `Wrapper` may be *owning* or *non-owning*, depending on how it's constructed.
An *owning* `Wrapper` will typically either take a previously allocated object via `std::unique_ptr<T>` or no pointer at all and itself allocate the object.
It will delete the wrapped object when destroyed.
A *non-owning* `Wrapper` may be used to register with the data repository objects that are not directly heap-allocated, for example data members of other objects.
It will take a raw pointer as input and not delete the wrapped object when destroyed.
