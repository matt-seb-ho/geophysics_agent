**Context:** Developerguide > Contributing > Doxygen > Build locally

## Build locally
Prior to configuring a GEOS build, have Doxygen installed:

  ``sh
   sudo apt install doxygen

.. note``
  Eventually, doxygen (version 1.8.13) is provided within the `thirdPartyLibs` repository.

Configure GEOS and go the build directory:

  ``sh
   cd GEOS/build-your-platform-release

Build doxygen docs only:

  ``sh
   make geosx_doxygen

Or build all docs:

  ``sh
   make geosx_docs

Open in browser:

  ``sh
   google-chrome html/doxygen_output/html/index.html
