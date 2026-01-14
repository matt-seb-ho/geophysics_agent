**Context:** Developerguide > Keycomponents > XML > Implement a `CatalogName` function (.hpp):

## Implement a `CatalogName` function (.hpp):
As explained above we add the class to the `ObjectCatalog` in two steps. First we implement the `CatalogName` function:


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_00
   :end-before: virtual

*[source: src/coreComponents/constitutive/relativePermeability/BrooksCoreyRelativePermeability.hpp]*

Then in the .cpp file we add the macro to register the catalog entry:


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_01
   :end-before: }

*[source: src/coreComponents/constitutive/relativePermeability/BrooksCoreyRelativePermeability.cpp]*

Now every time a "BrooksCoreyRelativePermeability" `string` is encountered inside a `Relative Permeability` catalog, we will instantiate a class `BrooksCoreyRelativePermeability`.
