**Context:** Functions > FunctionManager > Function Inputs and Application

## Function Inputs and Application
The inputs to each function type are specified via the `inputVarName` attribute.
These can either be the name of an array (e.g. "Pressure") or the special keyword "time" (time at the beginning of the current cycle).
If any of the input variables are vectors (e.g. "referencePosition"), the components will be given as function arguments in order.

In the .xml file, functions are referenced by name.
Depending upon the application, the functions may be applied in one of three ways:

1. Single application: 
   The function is applied to get a single scalar value.
   For example, this could define the flow rate applied via a BC at a given time.

2. Group application: 
   The function is applied to a (user-specified) ManagedGroup of size N.
   When called, it will iterate over the inputVarNames list and build function inputs from the group's wrappers.
   The resulting value will be a wrapper of size N.
   For example, this could be used to apply a user-defined constitutive relationship or specify a complicated boundary condition.

3. Statistics mode:
   The function is applied in the same manner as the group application, except that the function will return an array that contains the minimum, average, and maximum values of the results.


