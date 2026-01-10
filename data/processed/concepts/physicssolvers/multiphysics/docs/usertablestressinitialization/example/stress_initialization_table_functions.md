**Context:** Physicssolvers > Multiphysics > Usertablestressinitialization > Example > Stress Initialization Table Functions

## Stress Initialization Table Functions
The major distinction between this "user-defined" initialization and the "gravity-based" initialization is that in the user-defined case, the user provides the following additional information:

  - The distribution of effective stresses and pore pressure across the domain, with their gradients assumed constant along the depth in this example. We use a table function (see :ref:`FunctionManager`) to specify pressure and stress conditions throughout the area.


This is shown in the following tags under the `FieldSpecifications` section below


    :language: xml
    :start-after: <!-- SPHINX_USER_TABLES -->
    :end-before: <!-- SPHINX_USER_TABLES_END -->

The tables for `sigma_xx`, `sigma_yy`, `sigma_zz` and `init_pressure` are listed under the `Functions` section as shown below.


    :language: xml
    :start-after: <!-- SPHINX_FUNCTIONS -->
    :end-before: <!-- SPHINX_FUNCTIONS_END -->
    
The required input files: x.csv, y.csv, z.csv, effectiveSigma_xx.csv, effectiveSigma_yy.csv, effectiveSigma_zz.csv, and porePressure.csv are generated based on the expected stress-gradients in the model.

A Python script to generate these files is provided:

``console
  src/coreComponents/physicsSolvers/multiphysics/docs/userTableStressInitialization/genetrateTable.py

In addition to generating the files listed above, the script prints out the corresponding fluid density and rock density based on the model parameters provided. These values are then input into the `defaultDensity` parameter of the `CompressibleSinglePhaseFluid` and `ElasticIsotropic`` tags respectively, as shown below:


    :language: xml
    :start-after: <!-- SPHINX_Modify_Density -->
    :end-before: <!-- SPHINX_Modify_Density_END -->


    :language: xml
    :start-after: <!-- SPHINX_Modify_FluidDensity -->
    :end-before: <!-- SPHINX_Modify_FluidDensity_END -->


---------------------------------