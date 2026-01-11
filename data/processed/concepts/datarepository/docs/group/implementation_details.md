**Context:** Datarepository > Group > Implementation Details

## Implementation Details
Some noteworthy implementation details inside the declaration of `dataRepository::Group` are:


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_00
   :end-before: //END_SPHINX_INCLUDE_00
   
* In the GEOS repository, the `keyType` is specified to be a `string` for all  collection objects, 
  while the `indexType` is specified to be a `localIndex`.
  The types are set in the `common/DataTypes.hpp` file, but are typically a `string` and a 
  `std::ptrdiff_t` respectively.
  

   :language: c++
   :start-after: //START_SPHINX_INCLUDE_01
   :end-before: //END_SPHINX_INCLUDE_01
   
* The `subGroupMap` and `wrapperMap` aliases represent the type of container that the collection of 
  sub-`Group` s and `Wrapper` s are stored in for each `Group`.
  These container types are template specializations of the `MappedVector` class, which store a pointer to 
  a type, and provides functionality for a key or index based lookup. 
  More details may be found in the documentation for `MappedVector`.
  

   :language: c++
   :start-after: //START_SPHINX_INCLUDE_02
   :end-before: //END_SPHINX_INCLUDE_02
   
* The `m_parent` member is a pointer to the `Group` that contains the current `Group` as part of its
  collection of sub-`Group` s.

  
    Special care should be taken to avoid using this access whenever possible. 
    Remember...with great power comes great responsibility.
* The `m_wrappers` member is the collection of Wrappers contained in the current `Group`.
* The `m_subGroups` member is the collection of `Group` s contained in the current `Group`.
* The `m_size` and `m_capacity` members are used to set the size and capacity of any objects contained
  in the `m_wrappers` collection that have been specified to be set by their owning `Group`.
  This is typically only useful for Array types and is implemented within the `WrapperBase` object.
* The `m_name` member is the key of this Group in the collection of `m_parent->m_subGroups`.
  This key is unique in the scope of `m_parent`, so some is required when constructing the hierarchy.
  