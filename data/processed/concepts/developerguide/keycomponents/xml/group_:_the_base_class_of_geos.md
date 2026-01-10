**Context:** Developerguide > Keycomponents > XML > Group : the base class of GEOS

## Group : the base class of GEOS
All GEOS classes derive from a base class called `dataRepository::Group`.
The `Group` class provides a way to organize all GEOS objects in a filesystem-like structure.
One could think of `Group` s as *file folders* that can bear data (stored in `Wrapper` s), have a parent folder (another `Group`),  and have possibly multiple subfolders (referred to as the subgroups).
Below, we briefly review the data members of the `Group` class that are essential to understand the correspondence between the GEOS data structure and the XML input.
For more details, we refer the reader to the extensive documentation of the :ref:`dataRepository`, including the :ref:`Group` class documentation.


In the code listing below, we see that each `Group` object is at minimum equipped with the following member properties:

- A pointer to the parent `Group` called `m_parent` (member classes are prefixed by `m_`),
- The `Group` 's own data, stored for flexibility in an array of generic data `Wrapper` s called `m_wrappers`,
- A map of one or many children (also of type `Group`) called `m_subGroups`.
- The `m_size` and `m_capacity` members, that are used to set the size and capacity of any objects contained.
- The name of the `Group`, stored as a `string` in `m_name`. This name can be seen as the object unique ID.


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_02
   :end-before: RestartFlags

*[Source: src/coreComponents/dataRepository/Group.hpp]*

.. _ObjectCatalogPar:
