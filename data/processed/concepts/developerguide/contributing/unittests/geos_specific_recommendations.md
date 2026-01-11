**Context:** Developerguide > Contributing > UnitTests > GEOS Specific Recommendations

## GEOS Specific Recommendations
An informative example is `testSinglePhaseMobilityKernel` which tests the single phase flow mobility and accumulation kernels on a variety of inputs.


   :language: c++
   :start-after: // Sphinx start after test mobility
   :end-before: // Sphinx end before test mobility

*[Source: coreComponents/physicsSolvers/fluidFlow/kernels/singlePhase/unitTests/testSinglePhaseMobilityKernel.cpp]*

What makes this such a good test is that it depends on very little other than kernels themselves. There is no need to involve the data repository or parse an XML file. Sometimes however this is not possible, or at least not without a significant duplication of code. In this case it is better to embed the XML file into the test source as a string instead of creating a separate XML file and passing it to the test as a command line argument or hard coding the path. One example of this is `testLaplaceFEM` which tests the laplacian solver. The embedded XML is shown below.


   :language: c++
   :start-after: // Sphinx start after input XML
   :end-before: // Sphinx end before input XML

*[Source: coreComponents/integrationTests/fluidFlowTests/testCompMultiphaseFlow.cpp]*
