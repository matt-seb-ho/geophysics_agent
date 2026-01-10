**Context:** Developerguide > Keycomponents > XML > A few words about the ObjectCatalog

## A few words about the ObjectCatalog
**What is an ObjectCatalog and why do we need it?**

Some classes need external information (physical and/or algorithmic parameters for instance) provided by the user to be instantiated.
This is the case when the `m_input_flags` data member of one of the `Group` 's `Wrapper` s has an entry set to `REQUIRED` (we will illustrate this below).
In this situation, the required information must be supplied in the XML input file, and if it is absent, an error is raised by GEOS.

To connect the external (XML) and internal (C++) data structures, GEOS uses an **ObjectCatalog** that maps keys (of type `string`) to the corresponding classes (one unique key per mapped class).
These string keys, referred to as `catalogName` s, are essential to transfer the information from the XML file to the factory functions in charge of object instantiation (see below).

**What is a CatalogName?**

The `catalogName` of an object is a *key* (of type `string`) associated with this object's class.
On the one hand, in the XML file, the key is employed by the user as an XML tag to specify the type of object (e.g., the type of solver, constitutive model, etc) to create and use during the simulation.
On the other hand, internally, the key provides a way to access the appropriate factory function to instantiate an object of the desired class.

Most of the time, the `catalogName` and the C++ class name are identical.
This helps make the code easier to debug and allows the XML/C++ correspondence to be evident.
But strictly speaking, the `catalogName` can be anything, as long as it refers uniquely to a specific class.
The `catalogName` must not be confused with the object's *name* (`m_name` is a data member of the class that stores the object's unique ID, not its class key).
You can have several objects of the same class and hence the same `catalogName`, but with different names (i.e. unique ID): several fluid models, several solvers, etc.

**How can I add my new externally-accessible class to the ObjectCatalog?**

Let us consider a flow solver class derived from `FlowSolverBase`, that itself is derived from `PhysicsSolverBase`.
To instantiate and use this solver, the developer needs to make the derived flow solver class reachable from the XML file, via an XML tag.
Internally, this requires adding the derived class information to `ObjectCatalog`, which is achieved with two main ingredients: 1) a `CatalogName()` method in the class that lets GEOS know *what* to search for in the internal `ObjectCatalog` to instantiate an object of this class, 2) a macro that specifies *where* to search in the `ObjectCatalog`.

1. To let GEOS know what to search for in the catalog to instantiate an object of the derived class, the developer must equip the class  with a `CatalogName()` method that returns a `string`.
   In this document, we have referred to this returned `string` as the object's `catalogName`, but in fact, the method `CatalogName()` is what matters since the `ObjectCatalog` contains all the `CatalogName()` return values.
   Below, we illustrate this with the `CompositionalMultiphaseFlow` solver.
   The first code listing defines the class name, which in this case is the same as the `catalogName` shown in the second listing.


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_00
   :end-before: public:


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_01
   :end-before: virtual

*[Source: src/coreComponents/physicsSolvers/fluidFlow/CompositionalMultiphaseBase.hpp]*


2. To let GEOS know where to search in the `ObjectCatalog`, a macro needs to be added at the end of the .cpp file implementing the class.
   This macro (illustrated below) must contain the type of the base class (in this case, `PhysicsSolverBase`), and the name of the derived class (continuing with the example used above, this is `CompositionalMultiphaseFlow`).
   As a result of this construct, the `ObjectCatalog` is not a flat list of `string` s mapping the C++ classes.
   Instead, the `ObjectCatalog` forms a tree that reproduces locally the structure of the class diagram, from the base class to the derived classes.


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_01
   :end-before: //END_SPHINX_INCLUDE_01

*[Source: src/coreComponents/physicsSolvers/fluidFlow/CompositionalMultiphaseFVM.cpp]*




