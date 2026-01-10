**Context:** Tutorials > Step01 > Tutorial > Single-phase solver

## Single-phase solver
GEOS is a multiphysics simulator. To find the solution to different physical problems
such as diffusion or mechanical deformation, GEOS uses one or more physics solvers.
The `Solvers` tag is used to define and parameterize these solvers.
Different combinations of solvers can be applied
in different regions of the domain at different moments of the simulation.


In this first example, we use one type of solver in the entire domain and
for the entire duration of the simulation.
The input file for this tutorial can be found in the repository at
`inputFiles/singlePhaseFlow/3D_10x10x10_compressible_smoke.xml ](https://github.com/GEOS-DEV/GEOS/blob/6dd40e776556ec1235ba183e00796f2eedc035ac/inputFiles/singlePhaseFlow/3D_10x10x10_compressible_smoke.xml), which also includes
[inputFiles/singlePhaseFlow/3D_10x10x10_compressible_base.xml ](https://github.com/GEOS-DEV/GEOS/blob/6dd40e776556ec1235ba183e00796f2eedc035ac/inputFiles/singlePhaseFlow/3D_10x10x10_compressible_base.xml).
The solver we are specifying here is a single-phase flow solver.
In GEOS, such a solver is created using a `SinglePhaseFVM` element.
This type of solver is one among several cell-centered single-phase finite volume methods.


The XML block used to define this single-phase finite volume solver is shown here:


  :language: xml
  :start-after: <!-- SPHINX_TUT_INT_HEX_SOLVERS -->
  :end-before: <!-- SPHINX_TUT_INT_HEX_SOLVERS_END -->


Each type of solver has a specific set of parameters that are required and
some parameters that are optional. Optional values are usually set with sensible default values.

**name**

First, we register a solver of type [SinglePhaseFVM` with a user-chosen name,
here `SinglePhaseFlow`. This unique user-defined name can be almost anything.
However, some symbols are known to cause issues in names : avoid commas, slashes, curly braces.
GEOS is case-sensitive: it makes a distinction between two `SinglePhaseFVM` solvers called `mySolver` and `MySolver`.
Giving elements a name is a common practice in GEOS:
users need to give unique identifiers to objects they define.
That name is the handle to this instance of a solver class.

**logLevel**

Then, we set a solver-specific level of console logging (`logLevel` set to 1 here).
Notice that the value (1) is between double-quotes.
This is a general convention for all attributes:
we write `key="value"` regardless of the value type (integers, strings, lists, etc.).


For `logLevel`, higher values lead to more console output or intermediate results saved to files.
When debugging, higher `logLevel` values is often convenient.
In production runs, you may want to suppress most console output.


**discretization**

For solvers of the `SinglePhaseFVM` family, one required attribute is a discretization scheme.
Here, we use a Two-Point Flux Approximation (TPFA) finite volume discretization scheme called `singlePhaseTPFA`.
To know the list of admissible values of an attribute, please see `GEOS's XML schema ](https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/CompleteXMLSchema.html#).
This discretization type must know how to find permeability values that it uses internally to compute transmissibilities.
The `permeabilityNames` attribute tells the solver the user-defined name (the *handle*)
of the permeability values that will be defined elsewhere in the input file.
Note that the order of attributes inside an element is not important.

**fluidNames, solidNames, targetRegions**

Here, we specify a collection of fluids, rocks, and
target regions of the mesh on which the solver will apply.
Curly brackets are used in GEOS inputs to indicate collections of values (sets or lists).
The curly brackets used here are necessary, even if the collection contains a single value.
Commas are used to separate members of a set.

**Nested elements**

Finally, note that other XML elements can be nested inside the `Solvers` element.
Here, we use specific XML elements to set values for numerical tolerances.
The solver stops when numerical residuals are smaller than
the specified tolerances (convergence is achieved)
or when the maximum number of iterations allowed is exceeded (convergence not achieved).




.. _Mesh_tag_single_phase_internal_mesh:

------