**Context:** Physicssolvers > Multiphysics > Gravityinducedstressinitialization > Example > Initial and Boundary Conditions

## Initial and Boundary Conditions
The next step is to specify fields, including:

  - The initial value (hydrostatic equilibrium),
  - The boundary conditions (the displacement control of the outer boundaries have to be set).

In this problem, all outer boundaries of the domain are subject to roller constraints except the top of the model, left as a free surface.  

These boundary conditions are set up through the `FieldSpecifications` section.


    :language: xml
    :start-after: <!-- SPHINX_BC -->
    :end-before: <!-- SPHINX_BC_END -->


The parameters used in the simulation are summarized in the following table.

+------------------+-------------------------+------------------+--------------------+
| Symbol           | Parameter               | Unit             | Value              |
+==================+=========================+==================+====================+
| :math:[E`        | Young Modulus           | [MPa]            | 100                |
+------------------+-------------------------+------------------+--------------------+
| :math:`v`        | Poisson Ratio           | [-]              | 0.25               |
+------------------+-------------------------+------------------+--------------------+
| :math:`\rho_b`   | Bulk Density            | [kg/m\ :sup:`3`] | 2500               |
+------------------+-------------------------+------------------+--------------------+
| :math:`\phi`     | Porosity                | [-]              | 0.375              |
+------------------+-------------------------+------------------+--------------------+
| :math:`K_s`      | Grain Bulk Modulus      | [Pa]             | 10\ :sup:`27`      |
+------------------+-------------------------+------------------+--------------------+
| :math:`\kappa`   | Permeability            | [m\ :sup:`2`]    | 10\ :sup:`-12`     |
+------------------+-------------------------+------------------+--------------------+
| :math:`\rho_f`   | Fluid Density           | [kg/m\ :sup:`3`] | 1000               |
+------------------+-------------------------+------------------+--------------------+
| :math:`c_f`      | Fluid compressibility   | [Pa\ :sup:`-1`]  | 4.4x10\ :sup:`-10` |
+------------------+-------------------------+------------------+--------------------+
| :math:`\mu`      | Fluid viscosity         | [Pa s]           | 10\ :sup:`-3`      |
+------------------+-------------------------+------------------+--------------------+


---------------------------------