**Context:** Fileio > Doc > InputXMLFiles > VS Code

## VS Code
We recommend using the `XML ](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-xml) for validating xml files.
After installing this extension, you can associate GEOS format xml files by adding the following entry to the user settings file (replacing [systemId` with the correct path to the schema file):


 ```python
    {
        "xml.fileAssociations": [

            {
                "pattern": "**.xml",
                "systemId": "/path/to/GEOS/src/coreComponents/schema/schema.xsd"
            }
        ]
    }

