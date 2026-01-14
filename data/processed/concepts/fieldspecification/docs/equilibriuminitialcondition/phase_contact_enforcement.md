**Context:** Fieldspecification > EquilibriumInitialCondition > Phase Contact Enforcement

## Phase Contact Enforcement
Field data usually provide the depths of phase contacts with a high degree of certainty. Therefore, users want to enforce phase contacts precisely. 
Here, the method by which phase contacts are enforced is discussed. Firstly, we define phase contact as the depth at which the capillary pressure, :math:`p_c` is zero:



$z_{contact}$, $p_{nw}$ and $p_w$ refer to phase contact depth, non-wetting phase pressure and wetting phase pressure respectively.
A nested fixed-point iterative method is used to enforce phase contacts. Given a datum, where pressure of the "primary phase" is known, a phase contact and elevation points between the datum and the phase contact, the algorithm begins by marching from the datum to the phase contact. 
At the phase contact, pressure of "secondary phase" is equated to "primary phase" pressure and the "secondary phase" pressure is then corrected. The process is repeated until the pressure of the two phases at the phase contact are equal upto a tolerace.

# Composition Correction
Once phase pressures are computed during the hydrostatic equilibration step, capillary pressures are then determined. A capillary pressure model relates capillary pressure to the wetting phase saturation. 
Therefore, phase saturations can be back-calculated according to the capillary pressure model. To achieve this, a Newton-based solver is implemented that inverts capillary pressure to obtain the corresponding phase saturations. 
The capillary pressure inversion solver can handle three-phase systems and supports inversion for any generic capillary pressure model.

On the other hand, hydrostatic equilibration requires phase densities. Given a pressure, temperature and overall compositions, the fluid is flashed to obtain phase densities during each iteration of hydrostatic pressure computation. 
The other outputs of the flash are phase compositions, :math:`x_{ij}` and phase fractions, :math:`\gamma_j`. Phase saturations can then be computed from the phase densities and phase fractions. 
Lets denote these saturations as :math:`S_j^{flash}`` and the saturations from the capillary pressure inversion as :math:`S_j^{p_c}`. To account for capillary effects, :math:`S_j^{flash}` has to be equal to :math:`S_j^{p_c}`. 
This is achieved by recombining phases at the corrected overall compositions, without affecting the hydrostatic or thermodynamic equilibrium---the post-correction flash must yield the same density and phase compositions as before the correction. 
The choice of modifying the overall compositions stems from the fact that they are the least certain among the inputs to the flash. Phase fractions are modified using :math:`S_j^{p_c}` and phase densities from pre-correction flash:



The phases are then recombined using the corrected phase fractions and the phase compositions from pre-correction flash:



Note that volume change upon mixing is ignored.

# Single-phase flow parameters
For single-phase flow, the **HydrostaticEquilibrium** initialization procedure requires the following user input parameters:

* `datumElevation`: the elevation (in meters) at which the datum pressure is enforced. The user must ensure that the datum elevation is within the elevation range defined by the input mesh. GEOS issues a warning if this is not the case.

* `datumPressure`: the pressure value (in Pascal) enforced by GEOS at the datum elevation. 

* `objectPath`: the path defining the groups on which the hydrostatic equilibrium is computed. We recommend using `ElementRegions` to apply the hydrostatic equilibrium to all the cells in the mesh. Alternatively, the format `ElementRegions/NameOfRegion/NameOfCellBlock` can be used to select only a cell block on which the hydrostatic equilibrium is computed.



Using these parameters and the pressure-density constitutive relationship, GEOS uses a fixed-point iteration scheme to populate a table of hydrostatic pressures as a function of elevation. The fixed-point iteration scheme uses two optional attributes: `equilibriumTolerance`, the absolute tolerance to declare that the algorithm has converged, and `maxNumberOfEquilibrationTolerance`, the maximum number of iterations for a given elevation in the fixed point iteration scheme.

In addition, the elevation spacing of the hydrostatic pressure table is set with the optional `elevationIncrementInHydrostaticPressureTable` parameter (in meters), whose default value is 0.6096 meters. 
Then, once the table is fully constructed, the hydrostatic pressure in each cell is obtained by interpolating in the hydrostatic pressure table using the elevation at the center of the cell.



# Compositional multiphase flow parameters
For compositional multiphase flow, the **HydrostaticEquilibrium** initialization procedure follows the same logic but requires more input parameters.
In addition to the required `datumElevation`, `datumPressure`, and `objectPath` parameters listed above, the user must specify:

* `componentNames`: the names of the components present in the fluid model. This field is used to make sure that the components provided to **HydrostaticEquilibrium** are consistent with the components listed in the fluid model of the **Constitutive** block. 

* `componentFractionVsElevationTableNames`: the names of :math:`n_c` tables (where :math:`n_c` is the number of components) specifying the component fractions as a function of elevation. There must be one table name per component, and the table names must be listed in the same order as the components in `componentNames`. 

* `temperatureVsElevationTableName`: the names of the table specifying the temperature (in Kelvin) as a function of elevation.

* `initialPhaseName`: the name of the phase initially saturating the domain. The other phases are assumed to be at residual saturation at the beginning of the simulation. 

* `phaseContacts`: the elevation of the phase contacts. There must be :math:`n_p - 1` phase contacts (where :math:`n_p` is the number of phases). The phase contacts must be in descending order.

These parameters are used with the fluid density model (depending for compositional flow on pressure, component fractions, and in some cases, temperature) to populate the hydrostatic pressure table, and later initialize the pressure in each cell.





The full list of parameters is provided below:




# Examples
For single-phase flow, a typical hydrostatic equilibrium input looks like:

``xml
   <FieldSpecifications>
   
      <HydrostaticEquilibrium
        name="equil"
        objectPath="ElementRegions"      
        datumElevation="5"
        datumPressure="1e6"/>
      
   </FieldSpecifications>

For compositional multiphase flow, using for instance the CO2-brine flow model, a typical hydrostatic equilibrium input looks like:

``xml
   <FieldSpecifications>		
	     
      <HydrostaticEquilibrium
        name="equil"
        objectPath="ElementRegions"      
        datumElevation="28.5"
        datumPressure="1.1e7"
        initialPhaseName="water"
        componentNames="{ co2, water }"
        phaseContacts="{ 50 }"
        componentFractionVsElevationTableNames="{ initCO2CompFracTable,
                                                  initWaterCompFracTable }"
        temperatureVsElevationTableName="initTempTable"/>

   </FieldSpecifications>

In this case, a possible way to provide the three required tables is:

```xml
   <Functions>

     <TableFunction
       name="initCO2CompFracTable"
       coordinates="{ 0.0, 10.0, 20.0, 30.0 }"
       values="{ 0.04, 0.045, 0.05, 0.055 }"/>

     <TableFunction
       name="initWaterCompFracTable"
       coordinates="{ 0.0, 10.0, 20.0, 30.0 }"
       values="{ 0.96, 0.955, 0.95, 0.945 }"/>

     <TableFunction
       name="initTempTable"
       coordinates="{ 0.0, 15.0, 30.0 }"
       values="{ 358.15, 339.3, 333.03 }"/>
     
   </Functions>

Note that the spacing of the two component fraction tables must be the same, but the spacing of the temperature table can be different.

# Expected behavior and comparison with another initialization method
As illustrated in :ref:`TutorialFieldCase`, users can also use multiple **FieldSpecification** tags to impose initial fields, such as the pressure, component fractions, and temperature fields.
To help users select the initialization method that best meets their needs, we summarize and compare below the two possible ways to initialize complex, non-uniform initial fields for compositional multiphase simulations in GEOS.
