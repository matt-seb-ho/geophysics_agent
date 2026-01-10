**Context:** Fileio > Doc > InputXMLFiles > Symbolic Expressions

## Symbolic Expressions
Input XML files can also include symbolic mathematical expressions.
These are placed within pairs of backticks (\`), and use a limited python syntax.
Please note that parameters and units are evaluated before symbolic expressions.
While symbolic expressions are allowed within parameters, errors may occur if they are used in a way that results in nested symbolic expressions.
Also, note that residual alpha characters (e.g. `sin(`) are removed before evaluation for security.
The following shows an example of symbolic expressions:

```xml
  <Parameters>
    <Parameter name="a" value="2[m]"/>
    <Parameter name="b" value="1.2 [cm]"/>
    <Parameter name="c" value="3"/>
    <Parameter name="d" value="1.23e-4"/>
  </Parameters>
  <Geometry>
    <Box
      name="perf"
      xMin="{`$a$ - 0.2*$b$`, -1e6, -1e6}"
      xMax="{`$c$**2 / $d$`, 1e6, 1e6}" />
  </Geometry>

