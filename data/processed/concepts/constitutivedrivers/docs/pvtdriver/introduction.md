**Context:** Constitutivedrivers > PVTDriver > Introduction

## Introduction
When calibrating fluid material parameters to experimental or other reference data, it can be a hassle to launch a full flow simulation just to confirm density, viscosity, and other fluid properties are behaving as expected.  
Instead, GEOS provides a `PVTDriver` allowing the user to test fluid property models for a well defined set of pressure, temperature, and composition conditions.  
The driver itself is launched like any other GEOS simulation, but with a particular XML structure:

``sh
   ./bin/geosx -i myFluidTest.xml

This driver will work for any multi-phase fluid model (e.g. black-oil, co2-brine, compositional multiphase) enabled within GEOS.    
