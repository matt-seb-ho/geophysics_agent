**Context:** Fileio > Doc > InputXMLFiles > Schema Components

## Schema Components
The first entry in the schema are a set of headers the file type and version.
Following this, the set of available simple types for attributes are laid out.
Each of these includes a variable type name, which mirrors those used in the main code, and a regular expression, which is designed to match valid inputs.
These patterns are defined and documented in `rtTypes` (in `DataTypes.hpp`.
The final part of the schema is the file layout, beginning with the root `Problem`.
Each complex type defines an element, its children, and its attributes.
Each attribute defines the input name, type, default value, and/or usage.
Comments preceding each attribute are used to relay additional information to the users.

