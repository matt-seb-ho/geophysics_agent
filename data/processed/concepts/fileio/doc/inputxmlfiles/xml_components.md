**Context:** Fileio > Doc > InputXMLFiles > XML Components

## XML Components
The following illustrates some of the key features of a GEOS-format xml file:

``xml
    <?xml version="1.0" ?>

    <Problem>
        <BlockA
            someAttribute="1.234">

            <!-- Some comment -->
            <BlockB
              name="firstNamedBlock"
              anotherAttribute="0"/>
            <BlockB
              name="secondNamedBlock"
              anotherAttribute="1"/>
        </BlockA>
    </Problem>


The two basic components of an xml file are blocks, which are specified using angle brackets ("<BlockA>  </BlockA>"), and attributes that are attached to blocks (attributeName="attributeValue").
Block and attributes can use any ASCII character aside from `<`, `&`, `'`, and `"` (if necessary, use `&lt;`, `&amp;`, `&apos;`, or `&quot;`).
Comments are indicated as follows: `<!-- Some comment -->`.

At the beginning of a GEOS input file, you will find an optional xml declaration (`<?xml version="1.0" ?>`) that is used to indicate the format to certain text editors.
You will also find the root `Problem` block, where the GEOS configuration is placed.
Note that, aside from these elements and commented text, the xml format requires that no other objects exist at the first level.

In the example above, there is a single element within the `Problem` block: `BlockA`.
`BlockA` has an attribute `someAttribute`, which has a value of 1.234, and has three children: a commented string "Some comment" and two instances of `BlockB`.
The `name` attribute is required for blocks that allow multiple instances, and should include a unique string to avoid potential errors.
Where applicable these blocks will be executed in the order in which they are specified in input file.


# Input Validation
The optional `xmlns:xsi` and `xsi:noNamespaceSchemaLocation` attributes in the Problem block can be used to indicate the type of document and the location of the xml schema to the text editor:

``xml
    <Problem
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:noNamespaceSchemaLocation="/path/to/schema.xsd" />

The schema contains a list of xml blocks and attributes that are supported by GEOS, indicates whether a given object is optional or required, and defines the format of the object (string, floating point number, etc.).
A copy of the schema is included in the GEOS source code (/path/to/GEOS/src/coreComponents/schema/schema.xsd).
It can also be generated using GEOS: [geosx -s schema.xsd``

Many text editors can use the schema to help in the construction of an xml file and to indicate whether it is valid.
Using a validation tool is highly recommended for all users.
The following instructions indicate how to turn on validation for a variety of tools:

