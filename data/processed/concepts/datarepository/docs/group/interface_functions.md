**Context:** Datarepository > Group > Interface Functions

## Interface Functions
The public interface for `dataRepository::Group` provides functionality for constructing a hierarchy, 
and traversing that hierarchy, as well as accessing the contents of objects stored in the `Wrapper` 
containers stored within a `Group`.

#### Adding New Groups
To add new sub-`Group` s there are several `registerGroup` functions that add a new `Group` under
the calling `Group` scope.
A listing of these functions is provided:


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_REGISTER_GROUP
   :end-before: //END_SPHINX_INCLUDE_REGISTER_GROUP

These functions all take in a `name` for the new `Group`, which will be used as the key when trying to 
access the `Group` in the future.
Some variants create a new `Group`, while some variants take in an existing `Group` . 
The template argument is to specify the actaul type of the `Group` as it it is most likely a type that 
derives from `Group` that is we would like to create in the repository.
Please see the doxygen documentation for a detailed description of each option.

#### Getting Groups
The collection of functions to retrieve a `Group` and their descriptions are taken from source and shown 
here:


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_GET_GROUP
   :end-before: //END_SPHINX_INCLUDE_GET_GROUP


#### Register Wrappers

   :language: c++
   :start-after: //START_SPHINX_INCLUDE_REGISTER_WRAPPER
   :end-before: //END_SPHINX_INCLUDE_REGISTER_WRAPPER


#### Getting Wrappers/Wrapped Objects

   :language: c++
   :start-after: //START_SPHINX_INCLUDE_GET_WRAPPER
   :end-before: //END_SPHINX_INCLUDE_GET_WRAPPER
   
#### Looping Interface

   :language: c++
   :start-after: //START_SPHINX_INCLUDE_LOOP_INTERFACE
   :end-before: //END_SPHINX_INCLUDE_LOOP_INTERFACE

