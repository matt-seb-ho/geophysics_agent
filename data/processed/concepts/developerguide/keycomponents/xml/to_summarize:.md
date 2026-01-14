**Context:** Developerguide > Keycomponents > XML > To summarize:

## To summarize:
  - Every class in GEOS derive from a `Group` in a filesystem-like structure.
    A `Group` must have a parent `Group`, can have data (in `Wrapper` s), and can have one or many children (the subgroups).
    There is an `ObjectCatalog` in which the classes derived from `Group` are identified by a key called the `catalogName`.
  - When parsing XML input files, GEOS inspects each object's scope in the `ObjectCatalog` to find classes with the same `catalogName` as the XML tag.
    Once it finds an XML tag in the `ObjectCatalog`, it registers it inside the filesystem structure.
  - In the registration process, properties from the XML file are parsed and used to allocate member data `Wrapper` s and fully instantiate the `Group` class.
  - If XML tags are nested, subgroups are allocated and processed in a nested manner.

The correspondence between XML and class hierarchy is thus respected, and the internal object hierarchy mirrors the XML structure.



# Example: adding a new relative permeability model
This example is taken from the class `BrooksCoreyRelativePermeability`, derived from `RelativePermeabilityBase`.

