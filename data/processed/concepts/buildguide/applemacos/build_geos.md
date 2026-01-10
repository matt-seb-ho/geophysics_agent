**Context:** Buildguide > AppleMacOS > Build GEOS

## Build GEOS
.. code-block``
  cd ../../GEOS
  python3 scripts/config-build.py -hc host-configs/apple/macOS_arm.cmake -bt Release --ninja
  cd build-macOS_arm-release
  ninja geosx
