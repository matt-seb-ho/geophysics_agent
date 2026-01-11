**Context:** Constitutive > TwoPhaseImmiscibleFluid > Example using TableFunctions

# Example using TableFunctions
``xml
  <Constitutive>
    <TwoPhaseImmiscibleFluid
      name="fluid"
      phaseNames="{ oil, water }"
      densityTableNames="{ densityTableOil, densityTableWater }"
      viscosityTableNames="{ viscosityTableOil, viscosityTableWater }" />
  </Constitutive>

  <Functions>
    <TableFunction
      name="densityTableOil"
      coordinateFiles="{ pres_pvdo.txt }"
      voxelFile="dens_pvdo.txt"
      interpolation="linear" />

    <TableFunction
      name="viscosityTableOil"
      coordinateFiles="{ pres_pvdo.txt }"
      voxelFile="visc_pvdo.txt"
      interpolation="linear" />

    <TableFunction
      name="densityTableWater"
      coordinates="{ 2068000, 5516000, 30600000, 55160000 }"
      values="{ 980.683, 982.07, 992.233, 1002.265 }"
      interpolation="linear" />

    <TableFunction
      name="viscosityTableWater"
      coordinates="{ 0 }"
      values="{ 0.0003 }"
      interpolation="linear" />
  </Functions>  

