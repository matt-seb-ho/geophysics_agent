**Context:** Developerguide > Keycomponents > AddingNewSolver > Declaration file (reference)

## Declaration file (reference)
The included header is `physicsSolvers/simplePDE/LaplaceBaseH1.hpp` which declares the base class `LaplaceBaseH1`, shared by all Laplace solvers. Moreover, `physicsSolver/simplePDE/LaplaceBaseH1.hpp` includes the following headers:

 - `common/EnumStrings.hpp` which includes facilities for enum-string conversion (useful for reading enum values from input);
 - `physicsSolver/PhysicsSolverBase.hpp` which declares the abstraction class shared by all physics solvers.
 - `managers/FieldSpecification/FieldSpecificationManager.hpp` which declares a manager used to access and to set field on the discretized domain.

Let us jump forward to the class enum and variable as they contain the data used
specifically in the implementation of *LaplaceFEM*.

class enums and variables (reference)
````````````````````````````````````
The class exhibits two member variables:

 - `m_fieldName`` which stores the name of the diffused variable (*e.g.* the temperature) as a `string`;
 - `m_timeIntegrationOption` an `enum` value allowing to dispatch with respect to the transient treatment.

`TimeIntegrationOption` is an `enum` specifying the transient treatment which can be chosen
respectively between *SteadyState* and *ImplicitTransient* depending on whether we are interested in
the transient state.


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_TIMEINTOPT
   :end-before: //END_SPHINX_INCLUDE_TIMEINTOPT

In order to register an enumeration type with the Data Repository and have its value read from input,
we must define stream insertion/extraction operators. This is a common task, so GEOS provides
a facility for automating it. Upon including `common/EnumStrings.hpp`, we can call the following macro
at the namespace scope (in this case, right after the `LaplaceBaseH1` class definition is complete):


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_REGENUM
   :end-before: //END_SPHINX_INCLUDE_REGENUM

Once explained the main variables and enum, let us start reading through the different member functions:


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_BEGINCLASS
   :end-before: //END_SPHINX_INCLUDE_BEGINCLASS

Start looking at the class *LaplaceFEM* constructor and destructor declarations
shows the usual `string` `name` and `Group*` pointer to `parent` that are required
to build the global file-system like structure of GEOS (see :ref:`GroupPar` for details).
It can also be noted that the nullary constructor is deleted on purpose to avoid compiler
automatic generation and user misuse.

The next method `catalogName()` is static and returns the key to be added to the *Catalog* for this type of solver
(see :ref:`ObjectCatalogPar` for details). It has to be paired with the following macro in the implementation file.


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_REGISTER
   :end-before: //END_SPHINX_INCLUDE_REGISTER

Finally, the member function `registerDataOnMesh()` is declared in the `LaplaceBaseH1` class as


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_REGISTERDATAONMESH
   :end-before: //END_SPHINX_INCLUDE_REGISTERDATAONMESH

It is used to assign fields onto the discretized mesh object and
will be further discussed in the :ref:`Implementation` section.

The next block consists in solver interface functions. These member functions set up
and specialize every time step from the system matrix assembly to the solver stage.


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_SOLVERINTERFACE
   :end-before: //END_SPHINX_INCLUDE_SOLVERINTERFACE

Furthermore, the following functions are inherited from the base class.


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_SOLVERINTERFACE
   :end-before: //END_SPHINX_INCLUDE_SOLVERINTERFACE

Eventually, `applyDirichletBCImplicit()` is the working specialized member functions called
when `applyBoundaryConditions()` is called in this particular class override.

Browsing the base class `PhysicsSolverBase`, it can be noted that most of the solver interface functions are called during
either `PhysicsSolverBase::linearImplicitStep()` or `PhysicsSolverBase::nonlinearImplicitStep()` depending on the solver strategy chosen.

Switching to protected members, `postInputInitialization()` is a central member function and
will be called by `Group` object after input is read from XML entry file.
It will set and dispatch solver variables from the base class `PhysicsSolverBase` to the most derived class.
For `LaplaceFEM`, it will allow us to set the right time integration scheme based on the XML value
as will be further explored in the next :ref:`Implementation` section.

Let us focus on a `struct` that plays an important role: the *viewKeyStruct* structure.

*viewKeyStruct* structure (reference)
````````````````````````````````````

This embedded instantiated structure is a common pattern shared by all solvers.
It stores `dataRepository::ViewKey` type objects that are used as binding data
between the input XML file and the source code.


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_VIEWKEY
   :end-before: //END_SPHINX_INCLUDE_VIEWKEY

We can check that in the *LaplaceFEM* companion integratedTest


   :language: xml
   :start-after: <Solvers>
   :end-before: </Solvers>

In the following section, we will see where this binding takes place.

.. _Implementation:
