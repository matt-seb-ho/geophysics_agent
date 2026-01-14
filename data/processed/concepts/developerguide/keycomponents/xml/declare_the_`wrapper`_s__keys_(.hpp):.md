**Context:** Developerguide > Keycomponents > XML > Declare the `Wrapper` s  keys (.hpp):

## Declare the `Wrapper` s  keys (.hpp):
When attaching properties (i.e. data `Wrapper` s) to a class, a similar registration process must be done.
Every property is accessed through its `ViewKey` namespace.
In this namespace, we define `string` s that correspond to the tags of XML attributes of the "BrooksCoreyRelativePermeability" block.


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_01
   :end-before: //END_SPHINX_INCLUDE_01

*[source: src/coreComponents/constitutive/relativePermeability/BrooksCoreyRelativePermeability.hpp]*
