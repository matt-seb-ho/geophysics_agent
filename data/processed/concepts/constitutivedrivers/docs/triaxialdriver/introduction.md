**Context:** Constitutivedrivers > TriaxialDriver > Introduction

## Introduction
When calibrating solid material parameters to experimental data, it can be a hassle to launch a full finite element simulation to mimic experimental loading conditions.  Instead, GEOS provides a `TriaxialDriver` allowing the user to run loading tests on a single material point.  This makes it easy to understand the material response and fit it to lab data.  The driver itself is launched like any other GEOS simulation, but with a particular XML structure:

``sh
   ./bin/geosx -i myTest.xml

