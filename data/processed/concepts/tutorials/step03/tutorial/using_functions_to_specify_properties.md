**Context:** Tutorials > Step03 > Tutorial > Using functions to specify properties

## Using functions to specify properties
Eventually, one can define varying properties using `TableFunction` (:ref:`FunctionManager`) under the **Functions** tag:


  :language: xml
  :start-after: <!-- SPHINX_FIELD_CASE_TFUNC -->
  :end-before: <!-- SPHINX_FIELD_CASE_TFUNC_END -->

Here, the injection pressure is set to vary with time. Attentive reader might have
noticed that [sourceTerm` was bound to a `TableFunction` named *timeInj* under
**FieldSpecifications** tag definition. The initial pressure is set based on the values
contained in the table formed by the files which are specified. In particular,
the files *xlin.geos*, *ylin.geos* and *zlin.geos* define a regular meshing of
the bounding box containing the reservoir. The *pressure.geos* file then defines the values of the pressure at those points.

We proceed in a similar manner as for *pressure.geos* to map a heterogeneous permeability field (here the 5th layer of the SPE 10 test case) onto our unstructured grid. This mapping will use a nearest point interpolation rule.


   :width: 600px



------------------------------------