**Context:** Developerguide > Contributing > Doxygen > What to document

## What to document
The following entities declared in project header files within `geosx` namespace require documentation:

- all classes and structs, including public nested ones
- global functions, variables and type aliases
- public and protected member functions, variables and type aliases in classes
- preprocessor macros

Exceptions are made for:

- overrides of virtual functions in derived types
- implementation details nested in namespace `internal`
- template specializations in some cases
