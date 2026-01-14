**Context:** Tutorials > Step01 > Tutorial > Output

## Output
In order to retrieve results from a simulation,
we need to instantiate one or multiple [Outputs`.

Here, we define a single object of type `Silo`.
`Silo ](https://wci.llnl.gov/simulation/computer-codes/silo) is a library and a format for reading and writing a wide variety of scientific data.
Data in Silo format can be read by [VisIt ](https://wci.llnl.gov/simulation/computer-codes/visit/).

This `Silo` output object is called `siloOutput`.
We had referred to this object already in the `Events` section:
it was the target of a periodic event named `outputs`.
You can verify that the Events section is using this object as a target.
It does so by pointing to `/Outputs/siloOutput`.


  :language: xml
  :start-after: <!-- SPHINX_TUT_INT_HEX_OUTPUTS -->
  :end-before: <!-- SPHINX_TUT_INT_HEX_OUTPUTS_END -->


GEOS currently supports outputs that are readable by [VisIt
](https://wci.llnl.gov/simulation/computer-codes/visit/) and Kitware's Paraview, as well as other visualization tools.
In this example, we only request a Silo format compatible with VisIt.


All elements are now in place to run GEOS.


------------------------------------