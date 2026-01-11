**Context:** Datarepository > ObjectCatalog > Implementation Details

## Implementation Details
There are three key objects that are used to provide the ObjectCatalog functionality.

#### CatalogInterface
The `CatalogInterface` class provides the base definitions and interface for the 
ObjectCatalog concept.
It is templated on the common base class of all derived objects that are 
creatable by the "ObjectCatalog".
In addition, `CatalogInterface` is templated on a variadic parameter pack that 
allows for an arbitrary constructor argument list as shown in the declaration shown below:


   :language: c++
   :start-after: //START_SPHINX_0
   :end-before: {

The `CatalogInterface` also defines the actual catalog type using the template arguments:


   :language: c++
   :start-after: //START_SPHINX_1
   :end-before: //STOP_SPHINX

The `CatalogInterface::CatalogType` is a `std::unordered_map` with a string "key" and a value 
type that is a pointer to the CatalogInterface that represents a specific combination of 
`BASETYPE` and constructor arguments.

After from setting up and populating the catalog, which will be described in the "Usage" section, 
the only interface with the catalog will typically be when the `Factory()` method is called.
The definition of the method is given as:


   :language: c++
   :start-after: //START_SPHINX_2
   :end-before: //STOP_SPHINX

It can be seen that the static `Factory` method is simply a wrapper that calls the virtual 
`Allocate` method on a the catalog which is returned by `getCatalog()`.
The usage of the `Factory` method will be further discussed in the `Usage`_ section.


  the derived type and the `BASETYPE`. 
  This means that there is a single catalog for each combination of `BASETYPE` and the variadic 
  parameter pack representing the constructor arguments.
  In the future, we can investigate removing this restriction and allowing for construction of 
  a hierarchy of objects with an arbitrary constructor parameter list.

#### CatalogEntry
The `CatalogEntry` class derives from `CatalogInterface` and adds the a `TYPE` template argument
to the arguments of the `CatalogInterface`.


   :language: c++
   :start-after: //START_SPHINX_3
   :end-before: {

The `TYPE` template argument is the type of the object that you would like to be able to create 
with the "ObjectCatalog".
`TYPE` must be derived from `BASETYPE` and have a constructor that matches the variadic parameter
pack specified in the template parameter list.
The main purpose of the `CatalogEntry` is to override the `CatalogInterface::Allocate()` virtual 
function s.t. when key is retrieved from the catalog, then it is possible to create a new `TYPE`.
The `CatalogEntry::Allocate()` function is a simple creation of the underlying `TYPE` as shown by 
its definition:


   :language: c++
   :start-after: //START_SPHINX_4
   :end-before: //STOP_SPHINX

#### CatalogEntryConstructor
The `CatalogEntryConstructor` is a helper class that has a sole purpose of creating a 
new `CatalogEntry` and adding it to the catalog.
When a new `CatalogEntryConstructor` is created, a new `CatalogEntry` entry is created and
inserted into the catalog automatically.

