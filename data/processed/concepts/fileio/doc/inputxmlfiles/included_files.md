**Context:** Fileio > Doc > InputXMLFiles > Included Files

## Included Files
Both the XML preprocessor and GEOS executable itself provide the capability to build complex
multi-file input decks by including XML files into other XML files.

The files to be included are listed via the `<Included>` block. There maybe any number of such blocks.
Each block contains a list of `<File name="..."/>` tags, each indicating a file to include.
The `name` attribute must contain either an absolute or a relative path to the included file.
If the path is relative, it is treated as relative to the location of the referring file.
Included files may also contain includes of their own, i.e. it is possible to have `a.xml` include `b.xml`
which in turn includes `c.xml`.


   This applies both to XML includes, and to other types of file references (for example, table file names).
   Relative paths keep input decks both relocatable within the file system and sharable between users.

XML preprocessor's merging capabilities are more advanced than GEOS built-in ones.
Both are outlined below.

#### XML preprocessor
The merging approach is applied recursively, allowing children to include their own files.
Any potential conflicts are handled via the following scheme:

- Merge two objects if:
    - At the root level an object with the matching tag exists.
    - If the "name" attribute is present and an object with the matching tag and name exists.
    - Any preexisting attributes on the object are overwritten by the donor.
- Otherwise append the XML structure with the target.

#### GEOS
GEOS's built-in processing simply inserts the included files' content (excluding the root node)
into the XML element tree, at the level of `<Included>` tag. Partial merging is handled implicitly
by GEOS's data structure, which treats repeated top-level XML blocks as if they are one single block.
This is usually sufficient for merging together top-level input sections from multiple files,
such as multiple `<FieldSpecifications>` or `<Events>` sections, but more complex cases may require
the use of preprocessor.


   the XML schema currently produced by GEOS only allows a single such block, and only directly
   within the `<Problem>` tag. Inputs that use multiple blocks or nest them deeper may run but will
   fail to validate against the schema. This is a known discrepancy that may be fixed in the future.
