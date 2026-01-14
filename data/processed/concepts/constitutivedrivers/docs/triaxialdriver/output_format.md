**Context:** Constitutivedrivers > TriaxialDriver > Output Format

## Output Format
The `output` key is used to identify a file to which the results of the simulation are written.  If this key is omitted, or the user specifies `output="none"`, file output will be suppressed.  The file is a simple ASCII format with a brief header followed by test data:



  # column 1 = time
  # column 2 = axial_strain
  # column 3 = radial_strain_1
  # column 4 = radial_strain_2
  # column 5 = axial_stress
  # column 6 = radial_stress_1
  # column 7 = radial_stress_2
  # column 8 = newton_iter
  # column 9 = residual_norm
  0.0000e+00  0.0000e+00 0.0000e+00 0.0000e+00 -1.0000e+00 -1.0000e+00 -1.0000e+00 0.0000e+00 0.0000e+00
  1.6000e-01 -1.6000e-04 4.0000e-05 4.0000e-05 -1.1200e+00 -1.0000e+00 -1.0000e+00 2.0000e+00 0.0000e+00
  3.2000e-01 -3.2000e-04 8.0000e-05 8.0000e-05 -1.2400e+00 -1.0000e+00 -1.0000e+00 2.0000e+00 0.0000e+00
  ...

This file can be readily plotted using any number of plotting tools.  Each row corresponds to one timestep of the driver, starting from initial conditions in the first row.

We note that the file contains two columns for radial strain and two columns for radial stress.  For an isotropic material, the stresses and strains along the two radial axes will usually be identical.  We choose to output this way, however, to accommodate both anisotropic materials and true-triaxial loading conditions.  In these cases, the stresses and strains in the radial directions could potentially differ.

These columns can be added and subtracted to produce other quantities of interest, like mean stress or deviatoric stress.  For example, we can plot the output produce stress / strain curves (in this case for a plastic rather than simple elastic material):


   :width: 600px
   :align: center
   :alt: stress/strain figure
   :figclass: align-center

   Stress/strain behavior for a plastic material.

In this plot, we have reversed the sign convention to be consistent with typical experimental plots.  Note also that the `strainFunction` includes two unloading cycles, allowing us to observe both plastic loading and elastic unloading.
