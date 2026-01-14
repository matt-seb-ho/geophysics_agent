**Context:** Developerguide > Contributing > Caliper > GEOS/Caliper Annotation Macros

# GEOS/Caliper Annotation Macros
The following macros may be used to annotate GEOS:

* `GEOS_MARK_SCOPE(name)` - Marks a scope with the given name.
* `GEOS_MARK_FUNCTION` - Marks a function with the name of the function. The name includes the namespace the function is in but not any of the template arguments or parameters. Therefore overloaded function all show up as one entry. If you would like to mark up a specific overload use `GEOS_MARK_SCOPE` with a unique name. 
* `GEOS_MARK_BEGIN(name)` - Marks the beginning of a user defined code region. 
* `GEOS_MARK_END(name)`` - Marks the end of user defined code region.

The 2 first macros also generate annotations for NVTX is ENABLE_CUDA_NVTOOLSEXT is activated through CMake.
