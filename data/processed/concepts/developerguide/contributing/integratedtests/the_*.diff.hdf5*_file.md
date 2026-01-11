**Context:** Developerguide > Contributing > IntegratedTests > The *.diff.hdf5* File

## The *.diff.hdf5* File
Each error generated in the *restartcheck* step creates a group with three children in the *_diff.df5* file.
For example the error given above will generate a hdf5 group

``sh
  /FILENAME/datagroup_0000000/sidre/external/ProblemManager/domain/MeshBodies/mesh1/Level0/nodeManager/TotalDisplacement

with datasets *baseline*, *run* and *message* where *FILENAME* is the name of the restart data file being compared.
The *message* dataset contains a copy of the error message while *baseline* is a symbolic link to the baseline dataset and *run* is a sumbolic link to the dataset genereated by the run.
This allows for easy access to the raw data underlying the diff without data duplication. For example if you want to extract the datasets into python you could do this:

```python
  import h5py
  file_path = "beamBending_restart_000000003_diff.hdf5"
  path_to_data = "/beamBending_restart_000000011_0000000.hdf5/datagroup_0000000/sidre/external/ProblemManager/domain/MeshBodies/mesh1/Level0/nodeManager/TotalDisplacement"
  f = h5py.File("file_path", "r")
  error_message = f["path_to_data/message"]
  run_data = f["path_to_data/run"][:]
  baseline_data = f["path_to_data/baseline"][:]

  # Now run_data and baseline_data are numpy arrays that you may use as you see fit.
  rtol = 1e-10
  atol = 1e-15
  absolute_diff = np.abs(run_data - baseline_data) < atol
  hybrid_diff = np.close(run_data, baseline_data, rtol, atol)

When run in parallel each rank creates a *.$RANK.diff.hdf5* file which contains the diff of each data file processed by that rank.


.. _curve-check:

# Curve Check
This check compares time history (*.hdf5*) curves generated during GEOS execution against baseline and/or analytic solutions.
In contrast to restart checks, curve checks are designed to be flexible with regards to things like mesh construction, time stepping, etc.
The python script that evaluates the diff is included in the `geos_ats` package, and is located here: *integratedTests/scripts/geos_ats_package/geos_ats/helpers/curve_check.py*.
The script renders the curve check results as a figure, and will throw an error if curves are out of tolerance.
This script takes two positional arguments and a number of optional keyword arguments:

* filename : Path to the time history file.
* baseline : Path to the baseline file.
* -c/--curve : Add a curve to the check (value) or (value, setname).  Multiple curves are allowed.
* -s/--script : Python script instructions for curve comparisons (path, function, value, setname)
* -t/--tolerance : The tolerance for each curve check diffs (||x-y||/N).  Default is 0.
* -w/-Werror : Force warnings to be treated as errors, default is false.
* -o/--output : Output figures to this directory.  Default is ./curve_check_figures
* -n/--n-column : Number of columns to use for the output figure.  Default is 1.
* -u/--units-time : Time units for plots.  Options include milliseconds, seconds (default), minutes, hours, days, years


The curve check script begins by checking the target time history file for expected key values.
These include the time array ("value Time"), location array ("value ReferencePosition setname" or "value elementCenter setname"), and value array ("value setname").
Any missing values will be recorded as errors in the output.

The script will then run and record any user-requested python script instructions.
To do this, python will attempt to import the file given by *path* and evaluate the target function, which should accept the time history data as keyword arguments.
Note: to avoid side effects, please ensure that any imported scripts are appropriately guarded if they also allow direct execution:


```python
  if __name__ == '__main__':
    main()


This script will then check the size of the time history items, and will attempt to interpolate them if they do not match (currently, we only support interpolation in time).
Finally, the script will compare the time history values to the baseline values and any script-generated values.
If any curves do not match (`||x-y||/N > tol`), this will be recorded as an error.

