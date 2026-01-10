**Context:** Constitutivedrivers > PVTDriver > Output Format

## Output Format
The `output` key is used to identify a file to which the results of the simulation are written.  
If this key is omitted, or the user specifies `output="none"`, file output will be suppressed.  
The file is a simple ASCII format with a brief header followed by test data:



  # column 1 = time
  # column 2 = pressure
  # column 3 = temperature
  # column 4 = density
  # columns 5-6 = phase fractions
  # columns 7-8 = phase densities
  # columns 9-10 = phase viscosities
  0.0000e+00 1.0000e+06 3.5000e+02 1.5581e+01 1.0000e+00 4.1138e-11 1.5581e+01 1.0033e+03 1.7476e-05 9.9525e-04
  2.0408e-02 2.0000e+06 3.5000e+02 3.2165e+01 1.0000e+00 4.1359e-11 3.2165e+01 1.0050e+03 1.7601e-05 9.9525e-04
  4.0816e-02 3.0000e+06 3.5000e+02 4.9901e+01 1.0000e+00 4.1563e-11 4.9901e+01 1.0066e+03 1.7778e-05 9.9525e-04
  ...

Note that the number of columns will depend on how many phases and components are present and on whether the fluid is thermal or not.
In this case, we have a two-phase, two-component isothermal mixture.
The total density is reported in column 4, while phase fractions, phase densities, and phase viscosities are reported in subsequent columns.
If the `outputCompressibility` flag is activated, an extra column will be added for the total fluid compressibility after the density.
This is defined as :math:`c_t=\frac{1}{\rho_t}\left(\partial{\rho_t}/\partial P\right)` where :math:`\rho_t` is the total density.
If the `outputMassDensity` flag is activated, extra columns will be added for the mass density of each phase.
The number of columns will also depend on whether the `outputPhaseComposition` flag is activated or not. If it is activated, there will be an extra column for the mole fraction of each component in each phase.
The phase order will match the one defined in the input XML (here, the co2-rich phase followed by the water-rich phase).
This file can be readily plotted using any number of plotting tools.  Each row corresponds to one timestep of the driver, starting from initial conditions in the first row.
