**Context:** Developerguide > Contributing > IntegratedTests > Scalar Error Example

## Scalar Error Example
An error message for scalar values looks as follows

``sh
  Error: /datagroup_0000000/sidre/external/ProblemManager/domain/ConstitutiveManager/shale/YoungsModulus
    Scalar values of types float64 and float64 differ: 22500000000.0, 10000022399.9.

Where the first value is the value in the test's restart file and the second is the value in the baseline.

