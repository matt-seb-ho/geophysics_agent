**Context:** Fieldspecification > AquiferBoundaryCondition > Aquifer volumetric flow rate

## Aquifer volumetric flow rate
Let us consider a reservoir cell :math:`K` connected to aquifer :math:`A` through face :math:`f`, and the corresponding aquifer volumetric flow rate :math:`q^A_f` over time interval :math:`[ t^n, t^{n+1}]`.

The computation of :math:`q^A_f` proceeds as follows:



where :math:`\alpha^A_f` is the area fraction of face `f`, and :math:`p_K( t^{n+1} )` and :math:`p_K( t^n )` are the pressures in cell :math:`K` at time :math:`t^{n+1}` and time :math:`t^n`, respectively.

The area fraction of face :math:`f` with area :math:`|f|` is computed as:



The coefficient :math:`a` is computed as:



and the coefficient :math:`b` is given by the formula:



where :math:`\Delta \Phi^A_K( t^n_D ) := p^A - p_K( t^n ) - \rho^A_w g ( z_K - z^A )` is the potential difference between the reservoir cell and the aquifer at time :math:`t^n`, :math:`P_D( t_D )` is the dimensionless pressure evaluated at dimensionless time :math:`t_D`, :math:`P^{\prime}_D( t_D )` is the derivative of the dimensionless pressure with respect to dimensionless time, evaluated at dimensionless time :math:`t_D`.

The functional relationship of dimensionless pressure, :math:`P_D`, as a function of dimensionless time is provided by the user. A default table is also available, as shown below.
The cumulative aquifer flow rate, :math:`W^A( t^n_D )`, is an explicit quantity evaluated at :math:`t^n_D` and updated at the end of each converged time step using the formula:



with :math:`W^A( 0 ) := 0`. 
   
# Parameters
The main Carter-Tracy parameters and the expected units are listed below:

* `aquiferPorosity`: the aquifer porosity :math:`\phi^A`.

* `aquiferPermeability`: the aquifer permeability :math:`k^A` (in m2).

* `aquiferInitialPressure`: the aquifer initial pressure :math:`p^A` (in Pa), used to compute :math:`\Delta \Phi^A_K`.  

* `aquiferWaterViscosity`: the aquifer water viscosity :math:`\mu^A_w` (in Pa.s).

* `aquiferWaterDensity`: the aquifer water mass/molar density :math:`\rho^A_w` (in kg/m3 or mole/m3).

* `aquiferWaterPhaseComponentNames`: the name of the components in the water phase. These names must match the component names listed in the fluid model of the **Constitutive** block. This parameter is ignored in single-phase flow simulations.

* `aquiferWaterPhaseComponentFraction`: the aquifer component fractions in the water phase, :math:`y^A_{w,c}`. The components must be listed in the order of the components in `aquiferWaterPhaseComponentNames`. This parameter is ignored in single-phase flow simulations. 

* `aquiferTotalCompressibility`: the aquifer total compressibility (for the fluid and the solid) :math:`c^A_t` (in 1/Pa).    

* `aquiferElevation`: the elevation of the aquifer (in m).

* `aquiferThickness`: the thickness of the aquifer (in m).

* `aquiferInnerRadius`: the aquifer inner radius (in m).

* `aquiferAngle`: the angle subtended by the aquifer boundary from the center of reservoir (in degrees, must be between 0 and 360).
  
* `allowAllPhasesIntoAquifer`: flag controlling the behavior of the aquifer when there is flow from the reservoir to the aquifer. If the flag is equal to 1, all phases can flow into the aquifer. If the flag is equal to 0, only the water phase can flow into the aquifer. The default value of this optional parameter is 0. 

* `pressureInfluenceFunctionName`: the name of the table providing the dimensionless pressure as a function of dimensionless time. This table must be defined as a **TableFunction** in the **Functions** block of the XML file. If this optional parameter is omitted, a default pressure influence table is used. 
  
* `setNames`: the names of the face sets on which the aquifer boundary condition is applied.



The full list of parameters is provided below:



# Examples
Setting up the **Aquifer** boundary condition requires two additional pieces of information in the XML input file: a set of faces to specify where the aquifer boundary conditions will apply, and an aquifer tag that specifies the physical characteristics of the aquifer and determines how the boundary condition is applied.

1) To specify a set of faces: on simple grids, in the **Geometry** block of the XML file, we can define a **Box** that selects and assigns a name to a set of faces. To be included in a set, the faces must be fully enclosed in the **Box** (all vertices of a face must be inside the box for the face to be included to the set). The name of this box is a user-defined string, and it will be used in the aquifer tag to locate the face set. Here is an example of XML code to create such a face set from a box:

``xml
   <Geometry>
     ...
     <Box
       name="aquifer"
       xMin="{ 999.99, 199.99, 3.99 }"
       xMax="{ 1010.01, 201.01, 6.01 }"/> 
     ...
   </Geometry>
   

   
For more complex meshes, sch as those imported using the **VTKMesh**, using a **Box** to perform a face selection is challenging.
We recommend using a surface in the `vtk` file instead, which will be used to locate the face set.

2) To specify the aquifer characteristics: in the **FieldSpecifications** block of the XML file, we include an **Aquifer** tag. For single-phase flow, the aquifer definition looks like:

``xml
   <FieldSpecifications>
     ...
     <Aquifer
       name="aquiferBC"
       aquiferPorosity="2e-1"
       aquiferPermeability="3e-13"
       aquiferInitialPressure="9e6"
       aquiferWaterViscosity="0.00089"
       aquiferWaterDensity="962.81"
       aquiferTotalCompressibility="1e-10"
       aquiferElevation="4"
       aquiferThickness="18"
       aquiferInnerRadius="2000"
       aquiferAngle="20"
       setNames="{ aquifer }"/>
     ...
   </FieldSpecifications>     
		
For compositional multiphase flow, the user must include additional parameters to specify the water composition. We have additional influx controls over the aquifer with `allowAllPhasesIntoAquifer`. This is illustrated below for the CO2-brine fluid model:

``xml
   <FieldSpecifications>
     ...
     <Aquifer
       name="aquiferBC"
       aquiferPorosity="2e-1"
       aquiferPermeability="3e-13"
       aquiferInitialPressure="9e6"
       aquiferWaterViscosity="0.00089"
       aquiferWaterDensity="962.81"
       aquiferWaterPhaseComponentFraction="{ 0.0, 1.0 }"
       aquiferWaterPhaseComponentNames="{ co2, water }"
       aquiferTotalCompressibility="1e-10"
       aquiferElevation="4"
       aquiferThickness="18"
       aquiferInnerRadius="2000"
       aquiferAngle="20"
       allowAllPhasesIntoAquifer="1"
       setNames="{ aquifer }"/>
     ...
   </FieldSpecifications>

Finally, for both single-phase and multiphase flow, if a `pressureInfluenceFunctionName` attribute is specified in the **Aquifer** tag, a **TableFunction** must be included in the **Functions** block of the XML file as follows:

``xml
   <Functions>
     ...
     <TableFunction
       name="pressureInfluenceFunction"
       coordinates="{ 0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.5,
                      2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0,
		      50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 200.0, 800.0, 1600.0, 3200.0, 6400.0, 12800.0 }"
       values="{ 0.112, 0.229, 0.315, 0.376, 0.424, 0.469, 0.503, 0.564, 0.616, 0.659, 0.702, 0.735, 0.772, 0.802,
                 0.927, 1.02, 1.101, 1.169, 1.275, 1.362, 1.436, 1.5, 1.556, 1.604, 1.651, 1.829, 1.96, 2.067, 2.147,
		 2.282, 2.388, 2.476, 2.55, 2.615, 2.672, 2.723, 3.0537, 3.7468, 4.0934, 4.44, 4.7866, 5.1331 }"/>
     ...
   </Functions>


