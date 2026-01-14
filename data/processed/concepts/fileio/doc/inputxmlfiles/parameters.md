**Context:** Fileio > Doc > InputXMLFiles > Parameters

## Parameters
Parameters are a convenient way to build a configurable and human-readable input XML.
They are defined via a block in the XML structure.
To avoid conflicts with other advanced features, parameter names can include upper/lower case letters and underscores.
Parameters may have any value, including:

- Numbers (with or without units)
- A path to a file
- A symbolic expression
- Other parameters
- Etc.

They can be used as part of any input xml attribute as follows:

- $x_par$  (preferred)
- $x_par
- $:x_par
- $:x_par$

Attributes can be used across Included files, but cannot be used to set the names of included files themselves.
The following example uses parameters to set the root path for a table function, which is then scaled by another parameter:

```xml
  <Parameters>
    <Parameter
      name="flow_scale"
      value="0.5"/>
    <Parameter
      name="table_root"
      value="/path/to/table/root"/>
  </Parameters>
  
  <FieldSpecifications>
    <SourceFlux
      name="sourceTerm"
      objectPath="ElementRegions/Region1/block1"
      scale="$flow_scale$"
      functionName="flow_rate"
      setNames="{ source }"/>
  </FieldSpecifications>

  <Functions>
    <TableFunction
      name="flow_rate"
      inputVarNames="{time}"
      coordinateFiles="{$table_root$/time_flow.geos}"
      voxelFile="$table_root$/flow.geos"
      interpolation="linear"/>
  </Functions>

Any number of parameter overrides can be issued from the command line using the `-p name value` argument in the preprocessor script.
Note that if the override value contains any spaces, it may need to be surrounded by quotation marks (`-p name "paramter with spaces"`).
