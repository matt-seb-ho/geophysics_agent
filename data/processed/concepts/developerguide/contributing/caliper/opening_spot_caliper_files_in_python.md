**Context:** Developerguide > Contributing > Caliper > Opening Spot caliper files in Python

# Opening Spot caliper files in Python
An example Python program for analyzing Spot Caliper files in Python is provided below. Note that it requires `pandas` and `hatchet` both of which can be installed with a package manager. In addition it requires that `cali-query` is in the `PATH` variable, this is built with Caliper so we can just point it into the TPLs.

```Python
  import sys
  import subprocess
  import json
  import os

  import pandas as pd
  from IPython.display import display, HTML

  # Import hatchet, on LC this can be done by adding hatchet to PYTHONPATH
  sys.path.append('/usr/gapps/spot/live/hatchet')
  import hatchet as ht

  # Add cali-query to PATH
  cali_query_path = "/usr/gapps/GEOSX/thirdPartyLibs/2020-06-12/install-quartz-gcc@8.1.0-release/caliper/bin"
  os.environ["PATH"] += os.pathsep + cali_query_path

  CALI_FILES = [ 
  { "cali_file": "/usr/gapps/GEOSX/timingFiles/200612-04342891243.cali", "metric_name": "avg#inclusive#sum#time.duration"}, 
  { "cali_file": "/usr/gapps/GEOSX/timingFiles/200611-044740108300.cali", "metric_name": "avg#inclusive#sum#time.duration"}, 
  ]

  grouping_attribute = "prop:nested"
  default_metric = "avg#inclusive#sum#time.duration" 
  query = "select %s,sum(%s) group by %s format json-split" % (grouping_attribute, default_metric, grouping_attribute)

  gf1 = ht.GraphFrame.from_caliper(CALI_FILES[0]['cali_file'], query)
  gf2 = ht.GraphFrame.from_caliper(CALI_FILES[1]['cali_file'], query)

  # Print the tree representation using the default metric
  # Also print the resulting dataframe with metadata
  print(gf1.tree(color=True, metric="sum#"+default_metric))
  display(HTML(gf1.dataframe.to_html()))

  # Print the tree representation using the default metric
  # Also print the resulting dataframe with metadata
  print(gf2.tree(color=True, metric="sum#"+default_metric))
  display(HTML(gf2.dataframe.to_html()))

  # Compute the speedup between the first two cali files (exlusive and inclusive metrics only)
  gf3 = (gf1 - gf2) / gf2
  print(gf3.tree(color=True, metric="sum#"+default_metric))

  # Compute the difference between the first two cali files (exclusive and inclusive metrics only)
  # Print the resulting tree
  gf4 = gf1 - gf2
  print(gf4.tree(color=True, metric="sum#"+default_metric))

  # Compute the sum of the first two cali files (exclusive and inclusive metrics only)
  # Print the resulting tree
  gf5 = gf1 + gf2
  print(gf5.tree(color=True, metric="sum#"+default_metric))
