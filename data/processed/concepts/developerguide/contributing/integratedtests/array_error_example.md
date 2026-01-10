**Context:** Developerguide > Contributing > IntegratedTests > Array Error Example

## Array Error Example
An example of an error message for arrays is

``sh
  Error: /datagroup_0000000/sidre/external/ProblemManager/domain/MeshBodies/mesh1/Level0/nodeManager/TotalDisplacement
    Arrays of types float64 and float64 have 1836 values of which 1200 have differing values.
    Statistics of the differences greater than 0:
      max_index = (1834,), max = 2.47390764755, mean = 0.514503482629, std = 0.70212888881

This means that the max absolute difference is 2.47 which occurs at value 1834. Of the values that are not equal the mean absolute difference is 0.514 and the standard deviation of the absolute difference is 0.702.

When the tolerances are non zero the comparison is a bit more complicated. From the *FileComparison.compareFloatArrays* method documentation

``sh
  Entries x1 and x2 are  considered equal iff
      |x1 - x2| <= ATOL or |x1 - x2| <= RTOL * |x2|.
  To measure the degree of difference a scaling factor q is introduced. The goal is now to minimize q such that
      |x1 - x2| <= ATOL * q or |x1 - x2| <= RTOL * |x2| * q.
  If RTOL * |x2| > ATOL
      q = |x1 - x2| / (RTOL * |x2|)
  else
      q = |x1 - x2| / ATOL.
  If the maximum value of q over all the entries is greater than 1.0 then the arrays are considered different and an error message is produced.

An sample error message is

``sh
  Error: /datagroup_0000000/sidre/external/ProblemManager/domain/MeshBodies/mesh1/Level0/nodeManager/TotalDisplacement
    Arrays of types float64 and float64 have 1836 values of which 1200 fail both the relative and absolute tests.
      Max absolute difference is at index (1834,): value = 2.07474948094, base_value = 4.54865712848
      Max relative difference is at index (67,): value = 0.00215842135281, base_value = 0.00591771127792
    Statistics of the q values greater than 1.0 defined by the absolute tolerance: N = 1200
      max = 16492717650.3, mean = 3430023217.52, std = 4680859258.74
    Statistics of the q values greater than 1.0 defined by the relative tolerance: N = 0

