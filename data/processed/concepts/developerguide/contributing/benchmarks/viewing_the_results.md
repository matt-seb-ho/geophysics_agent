**Context:** Developerguide > Contributing > Benchmarks > Viewing the results

## Viewing the results
Each night the NightlyTests_ repository runs the benchmarks on both Quartz and Lassen, the `timingFiles` directory contains all of the resulting caliper output files. If you're on LC then these files are duplicated at `/usr/gapps/GEOSX/timingFiles/`` and if you have LC access you can view them in Spot_. You can also open these files in Python and analyse them (See :ref:`opening-spot-caliper-files-in-python`).

If you want to run the benchmarks on your local branch and compare the results with develop you can use the `benchmarks/compareBenchmarks.py` python script. This requires that you run the benchmarks on your branch and on develop. It will print out a table with the initialization time speed up and run time speed up, so a run speed up of of 2x means your branch runs twice as fast as develop where as a initialization speed up of 0.5x means the set up takes twice as long.



.. _NightlyTests: https://github.com/GEOS-DEV/NightlyTests
.. _Spot: https://lc.llnl.gov/spot2/?sf=/usr/gapps/GEOSX/timingFiles
