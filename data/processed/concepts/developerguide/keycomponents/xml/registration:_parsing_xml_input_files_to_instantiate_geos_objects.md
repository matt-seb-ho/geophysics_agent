**Context:** Developerguide > Keycomponents > XML > Registration: parsing XML input files to instantiate GEOS objects

## Registration: parsing XML input files to instantiate GEOS objects
In this section, we describe with more details the connection between **internal GEOS objects** and **external XML tags** parsed from parameter files.
We call this process *Registration*.
The registration process works in three steps:

  #. The XML document is parsed.
     Each time a new XML tag is found, the current local scope of the `ObjectCatalog` is inspected.
     The goal is to find a `catalogName` `string` that matches the XML tag.
  #. If it is the case (the current local scope of the `ObjectCatalog` contains a `catalogName` identical to the XML tag), then the code creates a new instance of the class that the `catalogName` refers to.
     This new object is inserted in the `Group` tree structure at the appropriate location, as a subgroup.
  #. By parsing the XML attributes of the tag, the new object properties are populated.
     Some checks are performed to ensure that the data supplied is conform, and that all the required information is present.


Let's look at this process in more details.

#### Creating a new object and giving it a Catalog name
Consider again that we are registering a flow solver deriving from `FlowSolverBase`, and assume that this solver is called `CppNameOfMySolver`.
This choice of name is not recommended (we want names that reflect what the solver does!), but for this particular example, we just need to know that this name is the class name inside the C++ code.

To specify parameters of this new solver from an XML file, we need to be sure that the XML tag and the `catalogName` of the class are identical.
Therefore, we equip the `CppNameOfMySolver` class with a `CatalogName()` method that returns the solver `catalogName` (=XML name).
Here, this method returns the `string`  "XmlNameOfMySolver".

We have deliberately distinguished the class name from the catalog/XML name for the sake of clarity in this example.
It is nevertheless a best practice to use the same name for the class and for the `catalogName`.
This is the case below for the existing `CompositionalMultiphaseFVM` class.


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_00
   :end-before: //END_SPHINX_INCLUDE_00


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_01
   :end-before: //END_SPHINX_INCLUDE_01

*[Source: src/coreComponents/physicsSolvers/fluidFlow/CompositionalMultiphaseFVM.hpp]*


#### Parsing XML and searching the ObjectCatalog in scope
Now that we have implemented a `CatalogName()` method returning a specific key (of type `string`), we can have a block in our XML input file with a tag that corresponds to the `catalogName` "XmlNameOfMySolver".
This is how the XML block would look like.

``xml
    <Problem>
      <Solvers
        gravityVector="{ 0.0, 0.0, -9.81 }">
        <XmlNameOfMySolver name="nameOfThisSolverInstance"
                                 verboseLevel="1"
                                 gravityFlag="1"
                                 temperature="297.15" />
          <LinearSolverParameters newtonTol="1.0e-6"
                                  maxIterNewton="15"
                                  useDirectSolver="1"/>
        </XmlNameOfMySolver>
      </Solvers>
    </Problem>

Here, we see that the XML structure defines a parent node "Problem", that has (among many others) a child node "Solvers".
In the "Solvers" block, we have placed the new solver block as a child node of the "Solvers" block with the XML tag corresponding to the `catalogName` of the new class.
We will see in details next how the GEOS internal structure constructed from this block mirrors the XML file structure.


#### Instantiating the new solver
Above, we have specified an XML block with the tag "XmlNameOfMySolver".
Now, when reading the XML file and encountering an "XmlNameOfMySolver" solver block, we add a new instance of the class `CppNameOfMySolver` in the filesystem structure as explained below.

We saw that in the XML file, the new solver block appeared as child node of the XML block "Solvers".
The internal construction mirrors this XML structure.
Specifically, the new object of class `CppNameOfMySolver` is registered as a subgroup (to continue the analogy used so far, as a subfolder) of its parent `Group`, the class `PhysicsSolverManager` (that has a `catalogName` "Solvers").
To do this, the method `CreateChild` of the `PhysicsSolverManager` class is used.


``cpp
    // Variable values in this example:
    // --------------------------------
    // childKey = "XmlNameOfMySolver" (string)
    // childName = "nameOfThisSolverInstance" (string)
    // PhysicsSolverBase::CatalogInterface = the Catalog attached to the base Solver class
    // hasKeyName = bool method to test if the childKey string is present in the Catalog
    // registerGroup = method to create a new instance of the solver and add it to the group tree


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_00
   :end-before: void

*[Source: src/coreComponents/physicsSolvers/PhysicsSolverManager.cpp]*

In the code listing above, we see that in the `PhysicsSolverManager` class, the `ObjectCatalog` is searched to find the `catalogName` "CompositionalMultiphaseFlow" in the scope of the `PhysicsSolverBase` class.
Then, the factory function of the base class `PhysicsSolverBase` is called.
The `catalogName` (stored in `childKey`) is passed as an argument of the factory function to ensure that it instantiates an object of the desired derived class.

As explained above, this is working because 1) the XML tag matches the `catalogName` of the `CompositionalMultiphaseFlow` class and 2) a macro is placed at the end of the .cpp file implementing the `CompositionalMultiphaseFlow` class to let the `ObjectCatalog` know that `CompositionalMultiphaseFlow` is a derived class of `PhysicsSolverBase`.

Note that several instances of the same type of solver can be created, as long as they each have a different name.


#### Filling the objects with data (wrappers)
After finding and placing the new solver `Group` in the filesystem hierarchy, properties are read and stored.
This is done by registering *data wrappers*.
We refer to the documentation of the :ref:`dataRepository` for additional details about the `Wrapper` s.
The method used to do that is called `registerWrapper` and is placed in the class constructor when the data is required in the XML file.
Note that some properties are registered at the current (derived) class level, and other properties can also be registered at a base class level.

Here, the only data (=wrapper) that is defined at the level of our `CppNameOfMySolver` class is temperature, and everything else is registered at the base class level.
We register a property of temperature, corresponding to the member class `m_temperature` of `CppNameOfMySolver`.
The registration also checks if a property is required or optional (here, it is required), and provides a brief description that will be used in the auto-generated code documentation.


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_00
   :end-before: Mass

*[Source: src/coreComponents/physicsSolvers/fluidFlow/CompositionalMultiphaseBase.cpp]*

This operation is done recursively if XML tags are nested.

