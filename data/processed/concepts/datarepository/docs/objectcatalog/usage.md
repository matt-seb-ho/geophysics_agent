**Context:** Datarepository > ObjectCatalog > Usage

## Usage
#### Creating A New Catalog
When creating a new "ObjectCatalog", it typically is done within the context of a specific
`BASETYPE`.
A simple example of a class hierarchy in which we would like to use the "ObjectCatalog"
to use to generate new objects is given in the unit test located in `testObjectCatalog.cpp`.

The base class for this example is defined as:


   :language: c++
   :start-after: //START_SPHINX_BASE
   :end-before: //STOP_SPHINX

There a couple of things to note in the definition of `Base`:

* `Base` has a convenience alias to use in place of the fully templated `CatalogInterface` name.
* `Base` defines a `getCatalog()` function that returns a static instantiation of a
  `CatalogInterface::CatalogType`.
  The `CatalogInterface::getCatalog()` function actually calls this function within the base
  class.
  This means that the base class actually owns the catalog, and the `CatalogInterface` is only
  operating on that `Base::getCatalog()`, and that the definition of this function is required.

#### Adding A New Type To The Catalog
Once a `Base` class is defined with the required features, the next step is to add a new derived
type to the catalog defined in `Base`.
There are three requirements for the new type to be registered in the catalog:

* The derived type must have a constructor with the arguments specified by the
  variadic parameter pack specified in the catalog.
* There must be a static function `static string catalogName()` that returns the
  name of the type that will be used to as keyname when it is registered `Base`'s catalog.
* The new type must be registered with the catalog held in `Base`. 
  To accomplish this, a convenience macro `REGISTER_CATALOG_ENTRY()` is provided.
  The arguments to this macro are the name type of Base, the type of the derived class,
  and then the variadic pack of constructor arguments.

A pair of of simple derived class that have the required methods are used in the unit test.


   :language: c++
   :start-after: //START_SPHINX_DERIVED1
   :end-before: //STOP_SPHINX


   :language: c++
   :start-after: //START_SPHINX_DERIVED2
   :end-before: //STOP_SPHINX

#### Allocating A New Object From The Catalog
The test function in the unit test shows how to allocate a new object of one 
of the derived types from `Factory` method.
Note the call to `Factory` is scoped by `Base::CatalogInterface`, which is 
an alias to the full templated instantiation of `CatalogInterface`.
The arguments for `Factory` 


   :language: c++
   :start-after: //START_SPHINX_TEST
   :end-before: //STOP_SPHINX

The unit test creates two new objects of type `Derived1` and `Derived2` using the 
catalogs `Factory` method.
Then the test checks to see that the objects that were created are of the correct type.
This unit test has some extra output to screen to help with understanding of the 
sequence of events.
The result of running this test is``
    $ tests/testObjectCatalog 
    Calling constructor for CatalogEntryConstructor< Derived1 , Base , ... >
    Calling constructor for CatalogInterface< Base , ... >
    Calling constructor for CatalogEntry< Derived1 , Base , ... >
    Registered Base catalog component of derived type Derived1 where Derived1::catalogName() = derived1
    Calling constructor for CatalogEntryConstructor< Derived2 , Base , ... >
    Calling constructor for CatalogInterface< Base , ... >
    Calling constructor for CatalogEntry< Derived2 , Base , ... >
    Registered Base catalog component of derived type Derived2 where Derived2::catalogName() = derived2
    Running main() from gtest_main.cc
    [==========] Running 1 test from 1 test case.
    [----------] Global test environment set-up.
    [----------] 1 test from testObjectCatalog
    [ RUN      ] testObjectCatalog.testRegistration
    EXECUTING MAIN
    Creating type Derived1 from catalog of Base
    calling Base constructor with arguments (1 3.14)
    calling Derived1 constructor with arguments (1 3.14)
    Creating type Derived2 from catalog of Base
    calling Base constructor with arguments (1 3.14)
    calling Derived2 constructor with arguments (1 3.14)
    EXITING MAIN
    calling Derived2 destructor
    calling Base destructor
    calling Derived1 destructor
    calling Base destructor
    [       OK ] testObjectCatalog.testRegistration (0 ms)
    [----------] 1 test from testObjectCatalog (0 ms total)
    
    [----------] Global test environment tear-down
    [==========] 1 test from 1 test case ran. (0 ms total)
    [  PASSED  ] 1 test.
    Calling destructor for CatalogEntryConstructor< Derived2 , Base , ... >
    Calling destructor for CatalogEntryConstructor< Derived1 , Base , ... >
    Calling destructor for CatalogEntry< Derived2 , Base , ... >
    Calling destructor for CatalogInterface< Base , ... >
    Calling destructor for CatalogEntry< Derived1 , Base , ... >
    Calling destructor for CatalogInterface< Base , ... >

In the preceding output, it is clear that the static catalog in `Base::getCatalog()`
is initialized prior the execution of main, and destroyed after the completion of main.
In practice, there have been no indicators of problems due to the use of a statically 
initialized/deinitialized catalog.

.. warning:
  The `catalog` is a static map, which means it is statically initialized and statically de-initialized.
  This results in a restriction in that no entry into the static map may depend on another object
  in the static map, nor on another static object in general.
  This is a well known issue with the use of static objects.
  However, this is generally not an issue in the "ObjectCatalog", as the catalog is populated with 
  `CatalogEntry`` objects, which are not dependent on other static objects.
